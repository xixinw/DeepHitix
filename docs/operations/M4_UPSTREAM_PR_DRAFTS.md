# M4 Upstream PR Drafts

Purpose: copy-ready PR bodies for the curated upstream patch series under `patches/hermes-agent-upstream-series/`.

Status: draft only. No upstream PR has been opened from this file.

## Series apply evidence

Fresh baseline sequential apply check passed for:

```text
0001-usage-normalization-and-deepseek-pricing.patch
0002-main-call-cost-telemetry-and-cli-gateway-display.patch
0003-deepseek-native-flash-pro-routing.patch
0004-context-continuity-extractive-checkpoint.patch
0005-cache-observability-hash-and-prefix-drift.patch
```

Result: all five patches applied with exit code 0; reject files: 0.

Full gate used across the final M2 + P0 + M3 scope:

```bash
python -m pytest tests/hermes_cli/test_deepseek_native_config.py tests/agent/test_routing_policy.py tests/agent/test_run_agent_cost_telemetry.py tests/agent/test_cost_telemetry.py tests/agent/test_usage_pricing.py tests/agent/test_auxiliary_main_first.py tests/agent/test_context_compressor.py tests/run_agent/test_deepseek_auxiliary_runtime.py tests/run_agent/test_plugin_context_engine_init.py -q -n 0
```

Result: `139 passed`.

---

## PR 1 — DeepSeek usage normalization and pricing

Patch:

```text
patches/hermes-agent-upstream-series/0001-usage-normalization-and-deepseek-pricing.patch
```

Suggested title:

```text
feat(deepseek): normalize usage and add current pricing coverage
```

Body:

```markdown
## Summary

- Normalize DeepSeek usage payloads for cache hit/miss and reasoning token counters.
- Add/refresh DeepSeek pricing aliases for `deepseek-chat`, `deepseek-reasoner`, `deepseek-v4-flash`, and `deepseek-v4-pro`.
- Cover cached DeepSeek calls so priced events do not silently fall back to unknown cost.

## Motivation

DeepSeek responses expose cache and reasoning usage fields differently from generic OpenAI-compatible providers. Without provider-aware normalization and pricing coverage, downstream telemetry can undercount cache hits or mark known DeepSeek calls as unpriced.

## Changes

- Update `agent/usage_pricing.py` usage normalization for DeepSeek cache/read/miss and reasoning token fields.
- Add current DeepSeek pricing aliases and cache-hit pricing behavior.
- Extend `tests/agent/test_usage_pricing.py` for usage normalization, pricing aliases, cache-hit tokens, and cached pricing status.

## Privacy / content-safety contract

- This PR only handles numeric usage and pricing metadata.
- It does not log prompts, assistant messages, tool results, headers, API keys, or request bodies.

## Test Plan

- [x] Targeted: `python -m pytest tests/agent/test_usage_pricing.py -q -n 0` -> `16 passed`
- [x] Full gate: `python -m pytest tests/hermes_cli/test_deepseek_native_config.py tests/agent/test_routing_policy.py tests/agent/test_run_agent_cost_telemetry.py tests/agent/test_cost_telemetry.py tests/agent/test_usage_pricing.py tests/agent/test_auxiliary_main_first.py tests/agent/test_context_compressor.py tests/run_agent/test_deepseek_auxiliary_runtime.py tests/run_agent/test_plugin_context_engine_init.py -q -n 0` -> `139 passed`
- [x] Patch hygiene: repo-relative paths only; no local absolute paths; non-empty diff hunks.
```

Reviewer notes:

- This PR is intentionally limited to usage/pricing. Telemetry writing and display are split into PR 2.

---

## PR 2 — Main-call cost telemetry and display surfaces

Patch:

```text
patches/hermes-agent-upstream-series/0002-main-call-cost-telemetry-and-cli-gateway-display.patch
```

Suggested title:

```text
feat(telemetry): add safe LLM call cost telemetry and runtime summaries
```

Body:

```markdown
## Summary

- Add append-only, allow-list based LLM call telemetry for successful main model calls.
- Surface compact cost/token/cache/latency summaries in CLI output.
- Add optional gateway runtime footer support for cost summaries.

## Motivation

Users need visibility into per-turn model cost, token usage, cache behavior, and latency without exposing prompt or response content. This lays the telemetry foundation for DeepSeek-native cost observability while keeping display surfaces privacy-safe.

## Changes

- Add `agent/cost_telemetry.py` with safe JSONL event building, sanitization, formatting, and best-effort append.
- Integrate main-call telemetry emission in `run_agent.py` after successful usage normalization and cost estimation.
- Add CLI per-turn cost/cache summary output for CLI platform runs.
- Add optional gateway footer cost display through `gateway/runtime_footer.py` and `gateway/run.py`.
- Add telemetry and gateway footer tests.

## Privacy / content-safety contract

Telemetry is allow-list based. The event builder and sanitizer intentionally exclude:

- prompts / request messages;
- assistant responses;
- tool results and tool outputs;
- headers, API keys, bearer tokens, cookies, passwords, and secrets;
- arbitrary unexpected fields.

The display summary is derived only from sanitized telemetry fields.

## Test Plan

- [x] Targeted: `python -m pytest tests/agent/test_cost_telemetry.py tests/agent/test_run_agent_cost_telemetry.py tests/gateway/test_runtime_footer.py -q -n 0` -> `45 passed`
- [x] Full gate: `python -m pytest tests/hermes_cli/test_deepseek_native_config.py tests/agent/test_routing_policy.py tests/agent/test_run_agent_cost_telemetry.py tests/agent/test_cost_telemetry.py tests/agent/test_usage_pricing.py tests/agent/test_auxiliary_main_first.py tests/agent/test_context_compressor.py tests/run_agent/test_deepseek_auxiliary_runtime.py tests/run_agent/test_plugin_context_engine_init.py -q -n 0` -> `139 passed`
- [x] Fresh apply: baseline + PR 1 + PR 2 applied cleanly.
- [x] Patch hygiene: repo-relative paths only; no local absolute paths; non-empty diff hunks.
```

Reviewer notes:

- This PR does not add Flash/Pro routing. Routing metadata fields are present, but routing behavior is introduced separately in PR 3.

---

## PR 3 — DeepSeek-native Flash/Pro routing

Patch:

```text
patches/hermes-agent-upstream-series/0003-deepseek-native-flash-pro-routing.patch
```

Suggested title:

```text
feat(deepseek): add configurable Flash/Pro routing policy
```

Body:

```markdown
## Summary

- Add a DeepSeek routing policy that defaults to Flash and supports explicit one-shot `/pro` escalation.
- Add config and CLI wiring for `deepseek_native.routing`.
- Ensure auxiliary text/compression tasks default to Flash when DeepSeek-native routing is enabled, instead of inheriting a Pro main-turn model.

## Motivation

DeepSeek-native usage benefits from routing ordinary turns to a lower-cost Flash model while allowing explicit user-controlled escalation to Pro. Auxiliary calls should remain cost-efficient and predictable unless explicitly overridden.

## Changes

- Add `agent/routing_policy.py` and routing policy tests.
- Add `deepseek_native.routing` config defaults in `hermes_cli/config.py`.
- Wire routing config through CLI agent construction and `AIAgent` initialization.
- Add `AIAgent._apply_turn_routing(...)` for default Flash and `/pro` one-shot Pro behavior.
- Add safe telemetry metadata for routing decision and escalation reason.
- Pass DeepSeek routing runtime to context compression / auxiliary resolution so text auxiliaries default to Flash.
- Add tests for routing policy, run_agent routing behavior, config surface, context compressor runtime propagation, auxiliary default Flash, and DeepSeek auxiliary runtime.

## Privacy / content-safety contract

- Routing telemetry emits enum-like metadata only: `routing_decision` and `escalation_reason`.
- `escalation_reason` uses fixed strings such as `explicit_pro_command`; it does not contain user prompt text.
- `/pro` command stripping returns sanitized message to the model, but sanitized prompt content is not copied into telemetry.

## Test Plan

- [x] Targeted: `python -m pytest tests/agent/test_routing_policy.py tests/agent/test_run_agent_cost_telemetry.py tests/agent/test_auxiliary_main_first.py tests/agent/test_context_compressor.py tests/run_agent/test_deepseek_auxiliary_runtime.py tests/hermes_cli/test_deepseek_native_config.py -q -n 0` -> `112 passed`
- [x] Full gate: `python -m pytest tests/hermes_cli/test_deepseek_native_config.py tests/agent/test_routing_policy.py tests/agent/test_run_agent_cost_telemetry.py tests/agent/test_cost_telemetry.py tests/agent/test_usage_pricing.py tests/agent/test_auxiliary_main_first.py tests/agent/test_context_compressor.py tests/run_agent/test_deepseek_auxiliary_runtime.py tests/run_agent/test_plugin_context_engine_init.py -q -n 0` -> `139 passed`
- [x] Fresh apply: baseline + PR 1 + PR 2 + PR 3 applied cleanly.
- [x] Patch hygiene: repo-relative paths only; no local absolute paths; non-empty diff hunks; no pycache artifacts.
```

Reviewer notes:

- This PR intentionally does not implement automatic escalation. It only supports explicit `/pro` and default Flash routing.

---

## PR 4 — Context continuity fallback on summary failure

Patch:

```text
patches/hermes-agent-upstream-series/0004-context-continuity-extractive-checkpoint.patch
```

Suggested title:

```text
fix(context): preserve continuity when summary generation fails
```

Body:

```markdown
## Summary

- Replace the static “summary unavailable” placeholder with an extractive checkpoint fallback when summary generation fails.
- Preserve active task context, file paths, tool call arguments, commands, and test output snippets from the compression window.
- Add regression tests for fallback continuity.

## Motivation

When summary LLM generation fails during context compression, inserting a generic placeholder loses the actionable state needed to continue work. An extractive checkpoint keeps enough non-generated context to resume the task safely.

## Changes

- Add `ContextCompressor._generate_extractive_checkpoint(...)`.
- Use the extractive checkpoint as the fallback summary when summary generation raises/fails.
- Add context compressor tests covering fallback content and ensuring the static placeholder no longer replaces useful continuity.

## Privacy / content-safety contract

- The fallback is built only from already-present conversation context that would otherwise be compressed.
- It is intended to preserve operational continuity, not introduce new telemetry or logging.
- It does not add new persistent storage of prompts, tool outputs, or secrets beyond the existing compressed conversation path.

## Test Plan

- [x] Targeted: `python -m pytest tests/agent/test_context_compressor.py -q -n 0` -> `82 passed`
- [x] Full gate: `python -m pytest tests/hermes_cli/test_deepseek_native_config.py tests/agent/test_routing_policy.py tests/agent/test_run_agent_cost_telemetry.py tests/agent/test_cost_telemetry.py tests/agent/test_usage_pricing.py tests/agent/test_auxiliary_main_first.py tests/agent/test_context_compressor.py tests/run_agent/test_deepseek_auxiliary_runtime.py tests/run_agent/test_plugin_context_engine_init.py -q -n 0` -> `139 passed`
- [x] Fresh apply: baseline + PR 1 + PR 2 + PR 3 + PR 4 applied cleanly.
- [x] Patch hygiene: repo-relative paths only; no local absolute paths; non-empty diff hunks.
```

Reviewer notes:

- The upstream patch was curated to include only extractive checkpoint fallback. A broader context-compressor diff was explicitly rejected because it mixed unrelated media/protect-head behavior.

---

## PR 5 — Cache observability hash and prefix drift telemetry

Patch:

```text
patches/hermes-agent-upstream-series/0005-cache-observability-hash-and-prefix-drift.patch
```

Suggested title:

```text
feat(telemetry): add cache observability hashes and prefix drift reason
```

Body:

```markdown
## Summary

- Add stable, content-safe hashes for active tool schema and immutable request prefix.
- Include `tool_schema_hash`, `immutable_prefix_hash`, and `prefix_drift_reason` in main-call telemetry.
- Add tests that verify hashes are stable and do not expose prompt, system, user, or tool schema text.

## Motivation

DeepSeek cache observability needs a way to diagnose cache misses caused by tool schema or stable-prefix drift without logging sensitive content. Hash-only telemetry provides the signal while preserving privacy.

## Changes

- Add `compute_tool_schema_hash(...)` and `compute_immutable_prefix_hash(...)` in `agent/cost_telemetry.py`.
- Extend the allow-listed telemetry schema with `prefix_drift_reason`.
- Include hash fields and drift reason in `build_llm_call_event(...)`.
- Update `AIAgent._emit_llm_call_telemetry(...)` to compute current hashes and compare with the previous main-call event.
- Add tests for stable hashes, content safety, and prefix drift enum behavior.

## Privacy / content-safety contract

Telemetry emits only:

- `sha256:<digest>` for tool schema surface;
- `sha256:<digest>` for leading system/developer immutable prefix;
- enum-like drift reason values such as `tool_schema_changed`, `immutable_prefix_changed`, or `tool_schema_and_immutable_prefix_changed`.

Telemetry intentionally does not emit:

- tool schema text;
- system/developer prompt content;
- user prompt content;
- old/new prefix values;
- assistant responses or tool results.

## Test Plan

- [x] Targeted: `python -m pytest tests/agent/test_cost_telemetry.py tests/agent/test_run_agent_cost_telemetry.py -q -n 0` -> `17 passed`
- [x] Full gate: `python -m pytest tests/hermes_cli/test_deepseek_native_config.py tests/agent/test_routing_policy.py tests/agent/test_run_agent_cost_telemetry.py tests/agent/test_cost_telemetry.py tests/agent/test_usage_pricing.py tests/agent/test_auxiliary_main_first.py tests/agent/test_context_compressor.py tests/run_agent/test_deepseek_auxiliary_runtime.py tests/run_agent/test_plugin_context_engine_init.py -q -n 0` -> `139 passed`
- [x] Fresh apply: baseline + PR 1 + PR 2 + PR 3 + PR 4 + PR 5 applied cleanly; reject files: 0.
- [x] Patch hygiene: repo-relative paths only; no local absolute paths; non-empty diff hunks.
```

Reviewer notes:

- The upstream patch was curated to exclude unrelated `run_agent.py` drift. An initial whole-file diff was rejected because it mixed MCP parallel and file-mutation verifier changes into this PR.
