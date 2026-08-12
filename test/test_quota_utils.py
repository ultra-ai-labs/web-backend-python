import importlib.util
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace


class FakeQuotaRepo:
    def __init__(self):
        self.quota = None

    def get_quota_by_user_id(self, user_id):
        return self.quota


def load_utils_module():
    fake_app = types.ModuleType('app')
    fake_app.__path__ = []
    fake_repo_package = types.ModuleType('app.repo')
    fake_repo_package.__path__ = []
    fake_quota_repo_module = types.ModuleType('app.repo.quota_repo')
    fake_quota_repo_module.QuotaRepo = FakeQuotaRepo

    module_names = ('app', 'app.repo', 'app.repo.quota_repo')
    previous_modules = {name: sys.modules.get(name) for name in module_names}
    sys.modules['app'] = fake_app
    sys.modules['app.repo'] = fake_repo_package
    sys.modules['app.repo.quota_repo'] = fake_quota_repo_module

    try:
        module_path = Path(__file__).parents[1] / 'app' / 'utils.py'
        spec = importlib.util.spec_from_file_location('quota_utils_under_test', module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        for name, previous_module in previous_modules.items():
            if previous_module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous_module


class CheckUserQuotaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.utils = load_utils_module()

    def set_quota(self, used, analysed, total):
        self.utils.quota_repo.quota = SimpleNamespace(
            used_quota=used,
            analysised_quota=analysed,
            total_quota=total,
        )

    def test_allows_collection_when_only_combined_statistics_exceed_total(self):
        self.set_quota(used=54322, analysed=45770, total=100000)

        allowed, message = self.utils.check_user_quota('admin-user-id')

        self.assertTrue(allowed)
        self.assertEqual(message, 'Success')

    def test_rejects_collection_when_used_quota_reaches_total(self):
        self.set_quota(used=100000, analysed=0, total=100000)

        allowed, message = self.utils.check_user_quota('admin-user-id')

        self.assertFalse(allowed)
        self.assertIn('(100000/100000)', message)

    def test_rejects_collection_when_used_quota_exceeds_total(self):
        self.set_quota(used=100001, analysed=0, total=100000)

        allowed, message = self.utils.check_user_quota('admin-user-id')

        self.assertFalse(allowed)
        self.assertIn('(100001/100000)', message)

    def test_analysis_statistics_do_not_change_the_quota_decision(self):
        self.set_quota(used=99999, analysed=0, total=100000)
        without_analysis = self.utils.check_user_quota('admin-user-id')
        self.set_quota(used=99999, analysed=999999, total=100000)
        with_analysis = self.utils.check_user_quota('admin-user-id')

        self.assertEqual(without_analysis, (True, 'Success'))
        self.assertEqual(with_analysis, without_analysis)


if __name__ == '__main__':
    unittest.main()
