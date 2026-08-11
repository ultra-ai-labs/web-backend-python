import unittest
import warnings
from types import SimpleNamespace
from unittest.mock import Mock, patch

warnings.filterwarnings(
    "ignore",
    message="urllib3 v2 only supports OpenSSL 1.1.1+",
)

import app.services.comment_analysis_service as analysis_module


class CommentAnalysisLlmTest(unittest.TestCase):
    def test_call_llm_rejects_missing_unified_key_before_client_creation(self):
        with patch.object(analysis_module.config, "LLM_API_KEY", ""), \
                patch.object(analysis_module, "OpenAI") as openai_client:
            with self.assertRaisesRegex(ValueError, "LLM_API_KEY"):
                analysis_module.call_llm([
                    {"role": "user", "content": "test"},
                ])
        openai_client.assert_not_called()

    def test_single_comment_analysis_uses_unified_llm_without_openai_key(self):
        service = analysis_module.CommentAnalysisService.__new__(
            analysis_module.CommentAnalysisService
        )
        comment = SimpleNamespace(
            content="测试评论",
            ip_location="上海",
            user_signature="",
            nickname="测试用户",
        )
        fields = [SimpleNamespace(key="意向客户", explanation="是或否")]

        with patch.object(analysis_module.config, "OPENAI_API_KEY", ""), \
                patch.object(
                    analysis_module,
                    "call_llm",
                    return_value='{"意向客户":"是"}',
                ) as call:
            result = service.gpt4_analysis(comment, "判断意向", fields)

        self.assertEqual('{"意向客户":"是"}', result)
        call.assert_called_once()

    def test_fallback_uses_default_result_without_http_request(self):
        service = analysis_module.CommentAnalysisService.__new__(
            analysis_module.CommentAnalysisService
        )
        service.douyin_comment_repo = Mock()
        comment = SimpleNamespace(
            comment_id="comment-1",
            content="测试评论",
            ip_location="上海",
            user_signature="",
            nickname="测试用户",
        )
        request = SimpleNamespace(analysis_request="判断意向")
        fields = [SimpleNamespace(key="分析理由", explanation="简短理由")]

        with patch("requests.post") as post:
            service.fallback_analysis(
                comment,
                "task-1",
                "dy",
                request,
                fields,
            )

        post.assert_not_called()
        service.douyin_comment_repo.update_comment_by_comment_id.assert_called_once_with(
            "comment-1",
            {"分析理由": "分析失败， 格式错误"},
            "task-1",
        )


if __name__ == "__main__":
    unittest.main()
