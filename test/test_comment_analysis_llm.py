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
    def test_call_llm_rejects_missing_provider_key_before_client_creation(self):
        with patch.object(
                analysis_module.config,
                "resolve_analysis_model_config",
                side_effect=ValueError(
                    "未配置 TOKENROUTER_API_KEY 或 DEEPSEEK_API_KEY"
                ),
        ), \
                patch.object(analysis_module, "OpenAI") as openai_client:
            with self.assertRaisesRegex(ValueError, "TOKENROUTER_API_KEY"):
                analysis_module.call_llm([
                    {"role": "user", "content": "test"},
                ])
        openai_client.assert_not_called()

    def test_call_llm_uses_selected_provider_configuration(self):
        selected = {
            "provider": "tokenrouter",
            "api_key": "tokenrouter-key",
            "base_url": "https://api.tokenrouter.cheap/v1",
            "model": "deepseek-v4-flash-0731",
        }
        response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="result"))]
        )

        with patch.object(
                analysis_module.config,
                "resolve_analysis_model_config",
                return_value=selected,
        ), patch.object(analysis_module, "OpenAI") as openai_client:
            openai_client.return_value.chat.completions.create.return_value = response
            result = analysis_module.call_llm([
                {"role": "user", "content": "test"},
            ])

        self.assertEqual("result", result)
        openai_client.assert_called_once_with(
            api_key="tokenrouter-key",
            base_url="https://api.tokenrouter.cheap/v1",
            max_retries=0,
            timeout=180,
        )
        openai_client.return_value.chat.completions.create.assert_called_once_with(
            model="deepseek-v4-flash-0731",
            messages=[{"role": "user", "content": "test"}],
            response_format={"type": "json_object"},
            max_tokens=12000,
            extra_body={"thinking": {"type": "disabled"}},
        )

    def test_comments_are_split_into_batches_of_one_hundred(self):
        comments = list(range(205))

        batches = list(analysis_module.chunked(comments, 100))

        self.assertEqual([100, 100, 5], [len(batch) for batch in batches])
        self.assertEqual(list(range(100)), batches[0])
        self.assertEqual(list(range(200, 205)), batches[2])

    def test_batch_messages_keep_every_comments_intent_and_reason_fields(self):
        comments = [
            {
                "comment_id": f"comment-{index}",
                "content": f"评论内容 {index}",
                "nickname": f"用户 {index}",
                "ip_location": "广东",
            }
            for index in range(100)
        ]
        fields = [
            {"key": "意向客户", "explanation": "是、否或不确定"},
            {"key": "分析理由", "explanation": "20字内简要说明理由"},
        ]

        messages = analysis_module.build_batch_messages(
            comments,
            "判断客户意向",
            fields,
        )

        payload = messages[1]["content"]
        self.assertIn('"comment_id": "comment-0"', payload)
        self.assertIn('"comment_id": "comment-99"', payload)
        self.assertIn("意向客户", messages[0]["content"])
        self.assertIn("分析理由", messages[0]["content"])
        self.assertIn("每条评论都必须", messages[0]["content"])

    def test_parse_batch_result_preserves_all_original_output_fields(self):
        raw_result = '''{
          "items": [
            {
              "comment_id": "comment-1",
              "意向客户": "是",
              "分析理由": "正在询问价格"
            },
            {
              "comment_id": "comment-2",
              "意向客户": "否",
              "分析理由": "没有购买意向"
            }
          ]
        }'''

        parsed = analysis_module.parse_batch_result(
            raw_result,
            ["comment-1", "comment-2"],
            ["意向客户", "分析理由"],
        )

        self.assertEqual(
            {
                "意向客户": "是",
                "分析理由": "正在询问价格",
            },
            parsed["comment-1"],
        )
        self.assertEqual(
            {
                "意向客户": "否",
                "分析理由": "没有购买意向",
            },
            parsed["comment-2"],
        )

    def test_batch_worker_calls_model_once_for_one_hundred_comments(self):
        comments = [
            {
                "comment_id": f"comment-{index}",
                "content": f"评论 {index}",
                "nickname": "用户",
                "ip_location": "广东",
            }
            for index in range(100)
        ]
        fields = [
            {"key": "意向客户", "explanation": "是、否或不确定"},
            {"key": "分析理由", "explanation": "简要说明"},
        ]
        response = {
            "items": [
                {
                    "comment_id": comment["comment_id"],
                    "意向客户": "否",
                    "分析理由": "没有购买意向",
                }
                for comment in comments
            ]
        }

        with patch.object(
                analysis_module,
                "call_llm",
                return_value=__import__("json").dumps(response, ensure_ascii=False),
        ) as call:
            result = analysis_module.analyze_comment_batch(
                comments,
                "判断客户意向",
                fields,
            )

        self.assertEqual(100, len(result))
        self.assertEqual(1, call.call_count)
        self.assertEqual("没有购买意向", result["comment-99"]["分析理由"])

    def test_batch_recovery_only_resends_missing_comments(self):
        comments = [
            {
                "comment_id": f"comment-{index}",
                "content": f"评论 {index}",
                "nickname": "用户",
                "ip_location": "广东",
            }
            for index in range(100)
        ]
        fields = [
            {"key": "意向客户", "explanation": "是、否或不确定"},
            {"key": "分析理由", "explanation": "简要说明"},
        ]
        first_result = {
            comment["comment_id"]: {
                "意向客户": "否",
                "分析理由": "没有购买意向",
            }
            for comment in comments[:-1]
        }
        missing_result = {
            "comment-99": {
                "意向客户": "是",
                "分析理由": "明确询问价格",
            }
        }

        with patch.object(
                analysis_module,
                "analyze_comment_batch",
                side_effect=[first_result, missing_result],
        ) as analyze:
            result = analysis_module.analyze_comment_batch_with_recovery(
                comments,
                "判断客户意向",
                fields,
            )

        self.assertEqual(100, len(result))
        self.assertEqual(2, analyze.call_count)
        retried_comments = analyze.call_args_list[1].args[0]
        self.assertEqual(["comment-99"], [item["comment_id"] for item in retried_comments])
        self.assertEqual("明确询问价格", result["comment-99"]["分析理由"])

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
