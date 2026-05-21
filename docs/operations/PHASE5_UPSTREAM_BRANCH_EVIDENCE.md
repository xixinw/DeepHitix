# Phase 5 Upstream PR Branch Evidence

Purpose: track real local PR branch creation against a fresh clone of `https://github.com/NousResearch/hermes-agent.git`.

Clone path:

```text
D:/Hermes_save/deepseek-native-agent/tmp/phase5-upstream-pr-branches/hermes-agent-upstream-clean
```

Fresh upstream HEAD at clone time:

```text
42c4288 fix(chat_completions): broaden tool_name strip docstring + AUTHOR_MAP
```

## Branch 1 — usage normalization and DeepSeek pricing

Branch:

```text
deepseek-native/0001-usage-normalization
```

Commit:

```text
ac472ba8f feat(deepseek): normalize usage and pricing
```

Files changed:

```text
agent/usage_pricing.py
tests/agent/test_usage_pricing.py
```

Note: direct `git apply --check patches/.../0001-...patch` failed against latest upstream HEAD because upstream drifted around `agent/usage_pricing.py` and `tests/agent/test_usage_pricing.py`. The branch was therefore reconstructed by copying the curated final versions of those two PR-1 files from the project Hermes snapshot, then committing only those files.

Validation:

```bash
python -m pytest tests/agent/test_usage_pricing.py -q -n 0 -o 'addopts='
```

Result:

```text
16 passed in 4.19s
```

Why `-o 'addopts='`: the fresh upstream checkout's `pyproject.toml` includes pytest addopts requiring plugins/options not available in this Windows local environment (`--timeout=30 --timeout-method=signal`). Clearing addopts matches the existing Windows workaround used in this project.

## Branch 2 — cost telemetry and display surfaces

Branch:

```text
deepseek-native/0002-cost-telemetry-display
```

Base:

```text
deepseek-native/0001-usage-normalization
```

Commit:

```text
5f562e8a3 feat(deepseek): add main call cost telemetry
```

Files changed:

- `agent/cost_telemetry.py`
- `run_agent.py`
- `agent/agent_init.py`
- `agent/conversation_loop.py`
- `gateway/runtime_footer.py`
- `gateway/run.py`
- `tests/agent/test_cost_telemetry.py`
- `tests/agent/test_run_agent_cost_telemetry.py`
- `tests/gateway/test_runtime_footer.py`

Porting note: direct patch application against latest upstream partly applied but produced 3 rejects in `run_agent.py`:

```text
Rejected hunk #3: reset _last_llm_call_event at turn start
Rejected hunk #4: emit telemetry after estimate_usage_cost(...)
Rejected hunk #5: return context_length + last_llm_call_event in result
```

Root cause: latest upstream has refactored the long `run_conversation()` loop out of `run_agent.py` into `agent/conversation_loop.py`, with session initialization in `agent/agent_init.py`. The branch therefore preserves PR-2 scope while adapting insertion points to upstream drift:

- keep `_emit_llm_call_telemetry(...)` on `AIAgent` in `run_agent.py` so existing tests can patch `run_agent.append_telemetry_event`;
- reset `_last_llm_call_event` in `agent/agent_init.py`, `AIAgent.reset_session_state(...)`, and at each `agent.conversation_loop.run_conversation(...)` turn start;
- emit one safe telemetry event in `agent/conversation_loop.py` immediately after `estimate_usage_cost(...)`;
- include `context_length` and `last_llm_call_event` in the conversation result for gateway footer rendering.

Validation:

```bash
python -m pytest tests/agent/test_usage_pricing.py tests/agent/test_cost_telemetry.py tests/agent/test_run_agent_cost_telemetry.py tests/gateway/test_runtime_footer.py -q -n 0 -o 'addopts='
```

Result:

```text
54 passed in 2.52s
```

Diff stat vs branch 1:

```text
agent/agent_init.py                          |   1 +
agent/conversation_loop.py                   |   9 ++
agent/cost_telemetry.py                      | 201 +++++++++++++++++++++++++++
gateway/run.py                               |   1 +
gateway/runtime_footer.py                    |  30 +++-
run_agent.py                                 |  47 +++++++
tests/agent/test_cost_telemetry.py           | 146 +++++++++++++++++++
tests/agent/test_run_agent_cost_telemetry.py | 102 ++++++++++++++
tests/gateway/test_runtime_footer.py         |  64 +++++++++
9 files changed, 597 insertions(+), 4 deletions(-)
```

Status after commit: working tree clean.

## Branch 3 — DeepSeek-native Flash/Pro routing

Branch:

```text
deepseek-native/0003-flash-pro-routing
```

Base:

```text
deepseek-native/0002-cost-telemetry-display
```

Commit:

```text
d8fec4b61 feat(deepseek): add flash pro routing
```

Files changed:

- `agent/routing_policy.py`
- `hermes_cli/config.py`
- `cli.py`
- `run_agent.py`
- `agent/agent_init.py`
- `agent/conversation_loop.py`
- `agent/context_compressor.py`
- `agent/auxiliary_client.py`
- routing/config/auxiliary/context/telemetry tests

Porting note: direct patch application against latest upstream partly applied but produced rejects in `run_agent.py`, `agent/context_compressor.py`, and `agent/auxiliary_client.py`:

```text
agent/auxiliary_client.py.rej: runtime fields + DeepSeek auxiliary default Flash hunk
agent/context_compressor.py.rej: update_model/__init__ routing runtime args hunk
run_agent.py.rej: old monolithic run_agent insertion points for init, context compressor, turn routing, and set_runtime_main
```

Root cause: latest upstream has split initialization and conversation loop responsibilities into `agent/agent_init.py` and `agent/conversation_loop.py`, and upstream auxiliary runtime handling added `auth_mode` / callable API-key preservation. The branch therefore preserves PR-3 scope while adapting insertion points to upstream drift:

- add `agent/routing_policy.py` and focused routing tests;
- thread DeepSeek routing config from config/CLI into `AIAgent` and `init_agent(...)`;
- keep routing state and `_apply_turn_routing(...)` on `AIAgent`;
- apply per-turn routing inside `agent/conversation_loop.py` before syncing `set_runtime_main(...)` so auxiliary clients see the routed model;
- pass routing runtime into context compressor and auxiliary auto resolution so DeepSeek-native side tasks default back to Flash after `/pro`;
- preserve upstream `auth_mode` and callable `api_key` behavior in `_normalize_main_runtime(...)`.

Validation:

```bash
python -m pytest tests/agent/test_routing_policy.py tests/hermes_cli/test_deepseek_native_config.py tests/run_agent/test_deepseek_auxiliary_runtime.py tests/agent/test_auxiliary_main_first.py tests/agent/test_context_compressor.py tests/agent/test_run_agent_cost_telemetry.py -q -n 0 -o 'addopts='
```

Result:

```text
112 passed in 9.69s
```

Diff stat vs branch 2:

```text
agent/agent_init.py                                | 18 +++++
agent/auxiliary_client.py                          | 18 ++++-
agent/context_compressor.py                        | 36 ++++++++--
agent/conversation_loop.py                         | 29 ++++----
agent/routing_policy.py                            | 81 ++++++++++++++++++++++
cli.py                                             |  5 ++
hermes_cli/config.py                               |  7 ++
run_agent.py                                       | 31 +++++++++
tests/agent/test_auxiliary_main_first.py           | 32 +++++++++
tests/agent/test_context_compressor.py             | 35 ++++++++++
tests/agent/test_routing_policy.py                 | 70 +++++++++++++++++++
tests/agent/test_run_agent_cost_telemetry.py       | 49 +++++++++++++
tests/hermes_cli/test_deepseek_native_config.py    |  9 +++
tests/run_agent/test_deepseek_auxiliary_runtime.py | 36 ++++++++++
14 files changed, 434 insertions(+), 22 deletions(-)
```

Status after commit: working tree clean.

## Branch 4 — Context continuity extractive checkpoint fallback

Branch:

```text
deepseek-native/0004-context-continuity-extractive-checkpoint-clean
```

Base:

```text
deepseek-native/0003-flash-pro-routing
```

Commit:

```text
1725964e6 fix(context): add extractive checkpoint fallback
```

Files changed:

- `agent/context_compressor.py`
- `tests/agent/test_context_compressor.py`

Porting note: direct patch application against latest upstream failed in `agent/context_compressor.py` and `tests/agent/test_context_compressor.py` because upstream context-compressor code already contains the newer `abort_on_summary_failure` split and nearby test wording/line numbers drifted. The branch keeps PR-4 scope narrow:

- add `_generate_extractive_checkpoint(...)` only;
- replace the default non-abort summary-failure placeholder with an extractive checkpoint;
- keep `compression.abort_on_summary_failure=true` behavior unchanged: compression aborts and preserves messages;
- update/add context-compressor tests only;
- do not include PR-5 cache observability or unrelated context/media/protect-head drift.

Validation:

```bash
python -m pytest tests/agent/test_context_compressor.py -q -n 0 -o 'addopts='
```

Result:

```text
85 passed in 7.17s
```

Diff stat vs branch 3:

```text
agent/context_compressor.py            | 84 +++++++++++++++++++++++++++-------
tests/agent/test_context_compressor.py | 54 +++++++++++++++++++++-
2 files changed, 120 insertions(+), 18 deletions(-)
```

Status after commit: working tree clean.

Note: clean branch-4/5 names are used because an intermediate local rebase attempt left the original branch-4/5 refs with duplicate ancestor commits; do not use those stale refs for PR creation.

## Branch 5 — Cache observability hashes and prefix drift

Branch:

```text
deepseek-native/0005-cache-observability-hash-prefix-drift-clean
```

Base:

```text
deepseek-native/0004-context-continuity-extractive-checkpoint-clean
```

Commit:

```text
1a8d29bd7 feat(telemetry): add cache observability hashes
```

Files changed:

- `agent/cost_telemetry.py`
- `run_agent.py`
- `tests/agent/test_cost_telemetry.py`
- `tests/agent/test_run_agent_cost_telemetry.py`

Porting note: `git apply --check patches/hermes-agent-upstream-series/0005-cache-observability-hash-and-prefix-drift.patch` succeeded against the clean branch-4 base. Scope is limited to PR-5 cache observability hashes / prefix drift; no unrelated context-compressor drift was added.

Validation:

```bash
python -m pytest tests/hermes_cli/test_deepseek_native_config.py tests/agent/test_routing_policy.py tests/agent/test_run_agent_cost_telemetry.py tests/agent/test_cost_telemetry.py tests/agent/test_usage_pricing.py tests/agent/test_auxiliary_main_first.py tests/agent/test_context_compressor.py tests/run_agent/test_deepseek_auxiliary_runtime.py tests/run_agent/test_plugin_context_engine_init.py tests/gateway/test_runtime_footer.py -q -n 0 -o 'addopts='
```

Result:

```text
170 passed in 14.25s
```

Diff stat vs clean branch 4:

```text
agent/cost_telemetry.py                      | 54 +++++++++++++++++++++++
run_agent.py                                 | 24 ++++++++++-
tests/agent/test_cost_telemetry.py           | 56 ++++++++++++++++++++++++
tests/agent/test_run_agent_cost_telemetry.py | 64 ++++++++++++++++++++++++++++
4 files changed, 197 insertions(+), 1 deletion(-)
```

Status after validation: working tree clean.
