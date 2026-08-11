# TokenRouter DeepSeek Flash Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Route all comment-analysis LLM calls through TokenRouter using `deepseek-v4-flash-0731`, with safe credential resolution and no fallback transmission to the legacy Replit proxy.

**Architecture:** Keep the existing OpenAI-compatible `call_llm(messages)` boundary. Extend configuration with a pure credential resolver, make single-comment and batch analysis use the same boundary, and make retry fallback local-only. Real credentials remain only in ignored `.env`; tracked files contain placeholders and tests.

**Tech Stack:** Python 3, `unittest`, `unittest.mock`, python-dotenv, OpenAI Python SDK 1.x, Flask, Docker Compose.

## Global Constraints

- TokenRouter API Base URL is exactly `https://api.tokenrouter.cheap/v1`.
- Public model ID is exactly `deepseek-v4-flash-0731`.
- Credential precedence is `LLM_API_KEY`, then `TOKENROUTER_API_KEY`, then `DEEPSEEK_API_KEY`.
- No real API key may appear in tracked files, logs, test output, or exceptions.
- No comment content may be sent to the legacy Replit model proxy.
- Do not add a frontend model selector, TokenRouter-specific SDK, streaming, Responses API, tools, or image input.
- Per `AGENTS.md`, create no intermediate commits; create at most one atomic commit after implementation, tests, documentation, and verification are complete.

---

## File Map

- Create `test/test_llm_config.py`: pure tests for credential precedence and empty configuration.
- Create `test/test_comment_analysis_llm.py`: service-level tests for unified calls, missing-key errors, and local-only fallback.
- Modify `test/test_model_service.py`: make the manual connectivity script use the same resolved `config.LLM_*` values.
- Modify `config/base_config.py`: define `resolve_llm_api_key()`, load `TOKENROUTER_API_KEY`, and produce `LLM_API_KEY`.
- Modify `app/services/comment_analysis_service.py`: validate unified credentials, remove the stale OpenAI gate/client, and remove the Replit fallback path.
- Modify `.env.example`: document TokenRouter credentials, Base URL, and model ID without secrets.
- Modify ignored `.env`: remove the stale provider-specific `LLM_API_KEY` override and switch `LLM_BASE_URL`/`LLM_MODEL` to TokenRouter.
- Keep `docs/superpowers/specs/2026-08-11-tokenrouter-deepseek-flash-design.md` and this plan as the design and execution record.

### Task 1: Credential Resolution

**Files:**
- Create: `test/test_llm_config.py`
- Modify: `config/base_config.py:71-81`

**Interfaces:**
- Consumes: `Mapping[str, str]` compatible environment values.
- Produces: `resolve_llm_api_key(environ=None) -> str`, `TOKENROUTER_API_KEY: str`, and the existing `LLM_API_KEY: str` constant.

- [ ] **Step 1: Write the failing credential-precedence tests**

```python
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
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
python3 -m unittest test.test_llm_config -v
```

Expected: import failure stating that `resolve_llm_api_key` is not defined in `config.base_config`.

- [ ] **Step 3: Implement the pure resolver and TokenRouter setting**

Add above the existing LLM constants in `config/base_config.py`:

```python
def resolve_llm_api_key(environ=None):
    source = os.environ if environ is None else environ
    return (
        source.get("LLM_API_KEY", "")
        or source.get("TOKENROUTER_API_KEY", "")
        or source.get("DEEPSEEK_API_KEY", "")
    )
```

Replace the current key constants with:

```python
# OPENAI配置（仅供仍需直连 OpenAI 的旧功能使用）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# DEEPSEEK 旧配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# TokenRouter 配置
TOKENROUTER_API_KEY = os.getenv("TOKENROUTER_API_KEY", "")

# 评论分析 LLM（OpenAI 兼容）
LLM_API_KEY = resolve_llm_api_key()
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-v4-flash")
```

- [ ] **Step 4: Run the focused test and verify GREEN**

Run:

```bash
python3 -m unittest test.test_llm_config -v
```

Expected: `Ran 4 tests` and `OK`.

### Task 2: Unified LLM Calls and Local-Only Fallback

**Files:**
- Create: `test/test_comment_analysis_llm.py`
- Modify: `app/services/comment_analysis_service.py:1-54,550-567,709-799`

**Interfaces:**
- Consumes: `call_llm(messages: list[dict[str, str]]) -> str` and existing comment/output-field objects.
- Produces: `CommentAnalysisService.gpt4_analysis(...) -> str` without an OpenAI-specific credential gate, and `fallback_analysis(...) -> None` that writes only a local default result.

- [ ] **Step 1: Write failing tests for missing keys, single analysis, and fallback isolation**

```python
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import app.services.comment_analysis_service as analysis_module


class CommentAnalysisLlmTest(unittest.TestCase):
    def test_call_llm_rejects_missing_unified_key_before_client_creation(self):
        with patch.object(analysis_module.config, "LLM_API_KEY", ""), \
                patch.object(analysis_module, "OpenAI") as openai_client:
            with self.assertRaisesRegex(ValueError, "LLM_API_KEY"):
                analysis_module.call_llm([{"role": "user", "content": "test"}])
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
                patch.object(analysis_module, "call_llm", return_value='{"意向客户":"是"}') as call:
            result = service.gpt4_analysis(comment, "判断意向", fields)

        self.assertEqual('{"意向客户":"是"}', result)
        call.assert_called_once()

    def test_fallback_uses_default_result_without_http_request(self):
        service = analysis_module.CommentAnalysisService.__new__(
            analysis_module.CommentAnalysisService
        )
        service.douyin_comment_repo = Mock()
        comment = SimpleNamespace(comment_id="comment-1")
        request = SimpleNamespace(analysis_request="判断意向")
        fields = [SimpleNamespace(key="分析理由", explanation="简短理由")]

        with patch("requests.post") as post:
            service.fallback_analysis(comment, "task-1", "dy", request, fields)

        post.assert_not_called()
        service.douyin_comment_repo.update_comment_by_comment_id.assert_called_once_with(
            "comment-1",
            {"分析理由": "分析失败， 格式错误"},
            "task-1",
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
python3 -m unittest test.test_comment_analysis_llm -v
```

Expected: failures showing that `call_llm` does not provide the required configuration error, `gpt4_analysis` rejects an empty OpenAI key, and fallback calls `requests.post`.

- [ ] **Step 3: Add unified-key validation**

Update `call_llm()` before client creation:

```python
def call_llm(messages):
    """调用由 config.LLM_* 配置的 OpenAI 兼容模型。"""
    if not config.LLM_API_KEY:
        raise ValueError(
            "未能获取到 LLM_API_KEY、TOKENROUTER_API_KEY 或 "
            "DEEPSEEK_API_KEY，请检查 .env 配置。"
        )
    client = OpenAI(
        api_key=config.LLM_API_KEY,
        base_url=config.LLM_BASE_URL,
        max_retries=2,
        timeout=60,
    )
    response = client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=messages,
    )
    return response.choices[0].message.content
```

- [ ] **Step 4: Remove the stale OpenAI gate from single-comment analysis**

Replace the beginning and end of `gpt4_analysis()` so it only builds messages and uses the unified boundary:

```python
def gpt4_analysis(self, comment, analysis_request, output_fields):
    comment_content = comment.content
    ip_location = comment.ip_location
    try:
        user_signature = comment.user_signature
    except Exception:
        user_signature = ""
    nickname = comment.nickname

    output_fields_str = "\n".join(
        [f"{field.key}: {field.explanation}" for field in output_fields]
    )
    system_prompt = f"""
            #任务背景和需求
            {analysis_request}

            # 结果
            请输出一个包含以下键的JSON对象：
            {output_fields_str}
            """
    user_prompt = self.create_prompt(
        comment_content, ip_location, user_signature, nickname
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    return call_llm(messages)
```

- [ ] **Step 5: Make fallback local-only and remove obsolete proxy helpers**

Replace `fallback_analysis()` with:

```python
def fallback_analysis(self, comment, task_id, platform, request, output_fields):
    utils.logger.info("模型分析重试失败，使用默认分析结果")
    json_result = self._generate_default_json_result(output_fields)
    if platform == "dy":
        self.douyin_comment_repo.update_comment_by_comment_id(
            comment.comment_id, json_result, task_id
        )
    else:
        self.xhs_comment_repo.update_comment_by_comment_id(
            comment.comment_id, json_result, task_id
        )
```

Delete `create_gpt4o_messages()` and `handle_gpt4o()`. Remove module-level `import openai` and `import requests` after verifying they have no remaining uses in this file.

- [ ] **Step 6: Run the service test and verify GREEN**

Run:

```bash
python3 -m unittest test.test_comment_analysis_llm -v
```

Expected: `Ran 3 tests` and `OK`.

- [ ] **Step 7: Run all new unit tests together**

Run:

```bash
python3 -m unittest test.test_llm_config test.test_comment_analysis_llm -v
```

Expected: `Ran 7 tests` and `OK`.

### Task 3: TokenRouter Environment and Tracked Configuration

**Files:**
- Modify: `.env` (ignored; never stage)
- Modify: `.env.example:54-66`
- Modify: `test/test_model_service.py:1-22`

**Interfaces:**
- Consumes: `TOKENROUTER_API_KEY` already supplied by the user in `.env`.
- Produces: runtime `config.LLM_BASE_URL == "https://api.tokenrouter.cheap/v1"` and `config.LLM_MODEL == "deepseek-v4-flash-0731"`.

- [ ] **Step 1: Update the tracked environment template**

Replace the current model-provider example block in `.env.example` with:

```env
# OpenAI API Key（仅供仍需直连 OpenAI 的旧功能使用）
OPENAI_API_KEY=your_openai_api_key

# DeepSeek 旧回退密钥
DEEPSEEK_API_KEY=your_deepseek_api_key

# TokenRouter API Key
TOKENROUTER_API_KEY=your_tokenrouter_api_key

# 评论分析 LLM（OpenAI 兼容）
# 密钥优先级：LLM_API_KEY > TOKENROUTER_API_KEY > DEEPSEEK_API_KEY
# TokenRouter DeepSeek V4 Flash-0731：
LLM_API_KEY=
LLM_BASE_URL=https://api.tokenrouter.cheap/v1
LLM_MODEL=deepseek-v4-flash-0731
```

- [ ] **Step 2: Switch the ignored local environment without exposing secrets**

Mechanically remove the stale `LLM_API_KEY=...` line from `.env`, leaving the already configured `TOKENROUTER_API_KEY` untouched. Replace only these non-secret settings:

```env
LLM_BASE_URL=https://api.tokenrouter.cheap/v1
LLM_MODEL=deepseek-v4-flash-0731
```

Do not print `.env`, and do not stage it.

- [ ] **Step 3: Align the manual connectivity script with production config**

Update `test/test_model_service.py` to import `config` and use `config.LLM_API_KEY`, `config.LLM_BASE_URL`, and `config.LLM_MODEL` rather than resolving keys independently. This keeps the manual connectivity script aligned with the production call path.

- [ ] **Step 4: Verify resolved runtime configuration without printing a secret**

Run:

```bash
python3 -c 'import config; print("LLM_BASE_URL=" + config.LLM_BASE_URL); print("LLM_MODEL=" + config.LLM_MODEL); print("LLM_API_KEY_CONFIGURED=" + str(bool(config.LLM_API_KEY)))'
```

Expected:

```text
LLM_BASE_URL=https://api.tokenrouter.cheap/v1
LLM_MODEL=deepseek-v4-flash-0731
LLM_API_KEY_CONFIGURED=True
```

- [ ] **Step 5: Verify the configured key can access the model list**

Run a Python command that creates `OpenAI(api_key=config.LLM_API_KEY, base_url=config.LLM_BASE_URL)`, lists models, and prints only:

```text
TOKENROUTER_MODEL_VISIBLE=True
```

The command must compare model IDs to `config.LLM_MODEL` and must not print the key or the full model-list response.

- [ ] **Step 6: Send a minimal non-user-data Chat request**

Run a Python command using the same client and:

```python
messages=[{"role": "user", "content": "只回复 OK"}]
```

Print only whether a non-empty response was received:

```text
TOKENROUTER_CHAT_RESPONSE_VALID=True
```

### Task 4: Full Verification and Atomic Commit

**Files:**
- Verify all files listed in the File Map.
- Stage tracked implementation, tests, design, and plan files only.

**Interfaces:**
- Consumes: the completed implementation and the configured ignored `.env`.
- Produces: verified working local TokenRouter integration and one atomic Git commit.

- [ ] **Step 1: Compile modified Python modules and tests**

Run:

```bash
python3 -m py_compile config/base_config.py app/services/comment_analysis_service.py test/test_llm_config.py test/test_comment_analysis_llm.py test/test_model_service.py
```

Expected: exit code 0 and no output.

- [ ] **Step 2: Run the complete focused regression suite**

Run:

```bash
python3 -m unittest test.test_llm_config test.test_comment_analysis_llm -v
```

Expected: `Ran 7 tests` and `OK`.

- [ ] **Step 3: Confirm the legacy proxy and stale gate are gone**

Run:

```bash
rg -n 'zg-cloud-model-service|OPENAI_API_KEY = config.OPENAI_API_KEY|handle_gpt4o' app/services/comment_analysis_service.py
```

Expected: exit code 1 with no matches.

- [ ] **Step 4: Review the tracked diff and secret boundary**

Run:

```bash
git status --short
git diff --check
git diff -- config/base_config.py app/services/comment_analysis_service.py .env.example test/test_llm_config.py test/test_comment_analysis_llm.py test/test_model_service.py docs/superpowers
git check-ignore .env
```

Expected: `.env` is ignored, `git diff --check` exits 0, no real keys appear in the diff, and only in-scope tracked files are staged later.

- [ ] **Step 5: Create the single authorized atomic commit**

Stage only the tracked files:

```bash
git add config/base_config.py app/services/comment_analysis_service.py .env.example test/test_llm_config.py test/test_comment_analysis_llm.py test/test_model_service.py docs/superpowers/specs/2026-08-11-tokenrouter-deepseek-flash-design.md docs/superpowers/plans/2026-08-11-tokenrouter-deepseek-flash.md
git commit -m "feat: route comment analysis through TokenRouter"
```

Expected: one commit containing the implementation, tests, environment template, design, and plan; ignored `.env` remains unstaged.
