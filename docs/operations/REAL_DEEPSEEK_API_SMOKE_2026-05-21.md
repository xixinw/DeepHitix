# Real DeepSeek API Smoke - 2026-05-21

Purpose: verify that the provided DeepSeek API credential can reach the live API before the published Docker image smoke.

Secret handling:

- The API key was used only as a transient process value.
- The key was not written to `.env`, docs, logs, or generated artifacts.
- This report intentionally does not include the key or request headers.

## Request

```text
endpoint: https://api.deepseek.com/chat/completions
model requested: deepseek-chat
prompt: "Please reply with OK only."
max_tokens: 8
temperature: 0
```

## Result

```text
HTTP_STATUS 200
MODEL deepseek-v4-flash
CONTENT_OK True
CONTENT_LEN 2
USAGE_KEYS completion_tokens,prompt_cache_hit_tokens,prompt_cache_miss_tokens,prompt_tokens,prompt_tokens_details,total_tokens
PROMPT_TOKENS_PRESENT True
COMPLETION_TOKENS_PRESENT True
```

## Interpretation

- The API key is valid for a minimal live DeepSeek chat completion.
- The DeepSeek service mapped the request to `deepseek-v4-flash`, matching the project default Flash route.
- Usage fields include cache hit/miss signals needed by the project's telemetry path.

This does not replace the required published-image Docker smoke. It only proves live DeepSeek API access from the current environment.
