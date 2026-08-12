import unittest

from config.base_config import resolve_analysis_model_config


class ResolveAnalysisModelConfigTest(unittest.TestCase):
    def test_tokenrouter_precedes_deepseek_and_ignores_legacy_llm_config(self):
        selected = resolve_analysis_model_config({
            "LLM_API_KEY": "llm-key",
            "LLM_BASE_URL": "https://legacy.example/v1",
            "LLM_MODEL": "legacy-model",
            "TOKENROUTER_API_KEY": "tokenrouter-key",
            "DEEPSEEK_API_KEY": "deepseek-key",
        })
        self.assertEqual({
            "provider": "tokenrouter",
            "api_key": "tokenrouter-key",
            "base_url": "https://api.tokenrouter.cheap/v1",
            "model": "deepseek-v4-flash-0731",
        }, selected)

    def test_deepseek_is_selected_only_when_tokenrouter_key_is_empty(self):
        selected = resolve_analysis_model_config({
            "TOKENROUTER_API_KEY": "  ",
            "DEEPSEEK_API_KEY": "deepseek-key",
        })
        self.assertEqual({
            "provider": "deepseek",
            "api_key": "deepseek-key",
            "base_url": "https://api.deepseek.com",
            "model": "deepseek-v4-flash",
        }, selected)

    def test_legacy_llm_key_alone_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "TOKENROUTER_API_KEY.*DEEPSEEK_API_KEY"):
            resolve_analysis_model_config({"LLM_API_KEY": "legacy-key"})

    def test_missing_provider_keys_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "TOKENROUTER_API_KEY.*DEEPSEEK_API_KEY"):
            resolve_analysis_model_config({})


if __name__ == "__main__":
    unittest.main()
