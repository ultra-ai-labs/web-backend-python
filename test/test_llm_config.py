import unittest

from config.base_config import resolve_llm_api_key


class ResolveLlmApiKeyTest(unittest.TestCase):
    def test_explicit_llm_key_has_highest_priority(self):
        key = resolve_llm_api_key({
            "LLM_API_KEY": "llm-key",
            "TOKENROUTER_API_KEY": "tokenrouter-key",
            "DEEPSEEK_API_KEY": "deepseek-key",
        })
        self.assertEqual("llm-key", key)

    def test_tokenrouter_key_precedes_deepseek_key(self):
        key = resolve_llm_api_key({
            "TOKENROUTER_API_KEY": "tokenrouter-key",
            "DEEPSEEK_API_KEY": "deepseek-key",
        })
        self.assertEqual("tokenrouter-key", key)

    def test_deepseek_key_is_the_legacy_fallback(self):
        key = resolve_llm_api_key({"DEEPSEEK_API_KEY": "deepseek-key"})
        self.assertEqual("deepseek-key", key)

    def test_missing_keys_return_empty_string(self):
        self.assertEqual("", resolve_llm_api_key({}))


if __name__ == "__main__":
    unittest.main()
