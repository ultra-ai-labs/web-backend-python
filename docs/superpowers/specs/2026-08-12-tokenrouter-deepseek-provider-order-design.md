# TokenRouter → DeepSeek Provider Order Design

## Goal

Remove the generic `LLM_*` credential path from backend model calls. Select the analysis provider only from provider-specific credentials, in this order:

1. `TOKENROUTER_API_KEY`
2. `DEEPSEEK_API_KEY`

## Provider selection

- When `TOKENROUTER_API_KEY` is non-empty, use `https://api.tokenrouter.cheap/v1` with `deepseek-v4-flash-0731`.
- Only when `TOKENROUTER_API_KEY` is absent or empty, use `DEEPSEEK_API_KEY` with `https://api.deepseek.com` and `deepseek-v4-flash`.
- Ignore `LLM_API_KEY`, `LLM_BASE_URL`, and `LLM_MODEL`, even when they remain in a legacy server environment.
- Provider selection happens before the request. A failed TokenRouter request must propagate its error and must not retry through DeepSeek.

## Code boundaries

`config/base_config.py` exposes one resolver returning the selected provider name, API key, base URL, and model. Both comment analysis and the legacy single-call backend entry point consume this resolver, so selection logic is not duplicated.

## Verification

Unit tests cover TokenRouter priority, DeepSeek selection when TokenRouter is absent, legacy `LLM_*` variables being ignored, missing provider credentials, and the OpenAI-compatible client receiving the selected provider configuration.
