# TokenRouter → DeepSeek Provider Order Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make backend model calls select TokenRouter first and direct DeepSeek only when the TokenRouter credential is not configured, without reading generic `LLM_*` variables.

**Architecture:** A single configuration resolver returns the provider-specific API key, base URL, and model. Existing model-call entry points consume that result and make exactly one provider request.

**Tech Stack:** Python 3, OpenAI-compatible Python SDK, unittest

## Global Constraints

- `TOKENROUTER_API_KEY` has priority over `DEEPSEEK_API_KEY`.
- A TokenRouter request failure does not trigger a DeepSeek request.
- `LLM_API_KEY`, `LLM_BASE_URL`, and `LLM_MODEL` do not participate in selection.
- TokenRouter uses `https://api.tokenrouter.cheap/v1` and `deepseek-v4-flash-0731`.
- Direct DeepSeek uses `https://api.deepseek.com` and `deepseek-v4-flash`.
- Produce one atomic commit only after implementation and verification, if committing is requested.

---

### Task 1: Provider resolver

**Files:**
- Modify: `config/base_config.py`
- Test: `test/test_llm_config.py`

**Interfaces:**
- Produces: `resolve_analysis_model_config(environ=None) -> dict[str, str]`

- [ ] Replace the old key-priority tests with tests for TokenRouter priority, DeepSeek fallback on missing configuration, ignored generic LLM variables, and missing provider keys.
- [ ] Run `python3 -m unittest test.test_llm_config -v` and confirm the new tests fail because the resolver does not exist.
- [ ] Implement the provider-specific resolver with fixed endpoints and models.
- [ ] Re-run `python3 -m unittest test.test_llm_config -v` and confirm all tests pass.

### Task 2: Backend consumers and environment example

**Files:**
- Modify: `app/services/comment_analysis_service.py`
- Modify: `main.py`
- Modify: `test/test_model_service.py`
- Modify: `.env.example`
- Test: `test/test_comment_analysis_llm.py`

**Interfaces:**
- Consumes: `resolve_analysis_model_config(environ=None) -> dict[str, str]`

- [ ] Update the comment-analysis tests to assert the selected provider configuration is passed to the OpenAI-compatible client.
- [ ] Run `python3 -m unittest test.test_comment_analysis_llm -v` and confirm the new test fails against the legacy `LLM_*` path.
- [ ] Change all backend model-call entry points to consume the resolver and make one request.
- [ ] Remove generic `LLM_*` variables from `.env.example` and document the provider order.
- [ ] Run the focused tests and then the full backend unittest suite.
