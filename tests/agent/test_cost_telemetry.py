import json

from agent.cost_telemetry import (
    append_telemetry_event,
    build_llm_call_event,
    compute_immutable_prefix_hash,
    compute_tool_schema_hash,
    format_llm_call_summary,
    sanitize_event,
)


def _event(**overrides):
    event = build_llm_call_event(
        provider="deepseek",
        api_mode="chat_completions",
        model="deepseek-v4-flash",
        call_type="main",
        prompt_tokens=1000,
        completion_tokens=200,
        cache_read_tokens=700,
        cache_miss_tokens=300,
        estimated_cost_usd=0.001,
        pricing_source="official_docs_snapshot",
        pricing_status="estimated",
        latency_ms=1234,
        routing_decision="flash",
        timestamp="2026-05-17T00:00:00Z",
    )
    event.update(overrides)
    return event


def test_build_llm_call_event_computes_cache_hit_ratio_and_total_tokens():
    event = build_llm_call_event(
        provider="deepseek",
        api_mode="chat_completions",
        model="deepseek-v4-flash",
        call_type="main",
        prompt_tokens=1000,
        completion_tokens=200,
        total_tokens=0,
        cache_read_tokens=700,
        cache_miss_tokens=300,
        timestamp="2026-05-17T00:00:00Z",
    )

    assert event["schema_version"] == 1
    assert event["event_type"] == "llm_call"
    assert event["provider"] == "deepseek"
    assert event["cache_read_tokens"] == 700
    assert event["cache_miss_tokens"] == 300
    assert event["cache_hit_ratio"] == 0.7
    assert event["total_tokens"] == 1200


def test_tool_schema_hash_is_stable_and_content_safe():
    tools_a = [
        {
            "type": "function",
            "function": {
                "name": "terminal",
                "description": "Run shell commands",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "SECRET_PROMPT_BODY must not leak"},
                    },
                },
            },
        },
        {"type": "function", "function": {"name": "read_file", "parameters": {"type": "object"}}},
    ]
    tools_b = list(reversed(tools_a))

    digest = compute_tool_schema_hash(tools_a)

    assert digest == compute_tool_schema_hash(tools_b)
    assert digest.startswith("sha256:")
    assert len(digest) == len("sha256:") + 64
    assert "terminal" not in digest
    assert "SECRET_PROMPT_BODY" not in digest


def test_immutable_prefix_hash_only_uses_stable_prefix_messages():
    base_messages = [
        {"role": "system", "content": "STABLE_SYSTEM_PROMPT"},
        {"role": "developer", "content": "STABLE_DEVELOPER_RULE"},
        {"role": "user", "content": "first user turn should not affect immutable prefix"},
    ]
    changed_user_messages = [
        base_messages[0],
        base_messages[1],
        {"role": "user", "content": "different user text SECRET_PROMPT_BODY"},
    ]
    changed_system_messages = [
        {"role": "system", "content": "CHANGED_SYSTEM_PROMPT"},
        base_messages[1],
        base_messages[2],
    ]

    digest = compute_immutable_prefix_hash(base_messages)

    assert digest == compute_immutable_prefix_hash(changed_user_messages)
    assert digest != compute_immutable_prefix_hash(changed_system_messages)
    assert digest.startswith("sha256:")
    assert "STABLE_SYSTEM_PROMPT" not in digest
    assert "SECRET_PROMPT_BODY" not in digest


def test_append_telemetry_event_creates_parent_and_appends_jsonl(tmp_path):
    path = tmp_path / "nested" / "usage.jsonl"

    assert append_telemetry_event(_event(), path=path) is True
    assert append_telemetry_event(_event(session_id="s2"), path=path) is True

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    second = json.loads(lines[1])
    assert first["model"] == "deepseek-v4-flash"
    assert second["session_id"] == "s2"


def test_append_telemetry_event_write_failure_does_not_raise(tmp_path):
    path = tmp_path / "as_dir"
    path.mkdir()

    assert append_telemetry_event(_event(), path=path) is False


def test_sanitize_event_drops_prompt_response_and_secret_fields():
    event = _event(
        prompt="do not log me",
        messages=[{"role": "user", "content": "secret prompt"}],
        assistant_content="do not log response",
        api_key="sk-secret",
        authorization="Bearer secret",
        unexpected="drop me",
    )

    safe = sanitize_event(event)

    assert safe["model"] == "deepseek-v4-flash"
    assert "prompt" not in safe
    assert "messages" not in safe
    assert "assistant_content" not in safe
    assert "api_key" not in safe
    assert "authorization" not in safe
    assert "unexpected" not in safe


def test_append_telemetry_event_writes_no_prompt_or_secret_payload(tmp_path):
    path = tmp_path / "usage.jsonl"
    event = _event(prompt="my prompt", api_key="sk-secret", content="assistant body")

    assert append_telemetry_event(event, path=path) is True
    raw = path.read_text(encoding="utf-8")

    assert "my prompt" not in raw
    assert "sk-secret" not in raw
    assert "assistant body" not in raw
    stored = json.loads(raw)
    assert stored["provider"] == "deepseek"


def test_format_llm_call_summary_shows_cost_tokens_cache_and_latency():
    summary = format_llm_call_summary(
        _event(
            prompt_tokens=1000,
            completion_tokens=200,
            total_tokens=1200,
            cache_read_tokens=700,
            cache_write_tokens=10,
            estimated_cost_usd=0.00023,
            pricing_status="estimated",
            latency_ms=1234,
            prompt="do not leak prompt",
            assistant_content="do not leak response",
        )
    )

    assert "Turn cost: ~$0.0002" in summary
    assert "tokens 1,200" in summary
    assert "cache 700/1,000 (70% hit, 10 written)" in summary
    assert "latency 1.2s" in summary
    assert "do not leak" not in summary


def test_format_llm_call_summary_marks_unknown_pricing():
    summary = format_llm_call_summary(
        _event(
            model="local/model",
            estimated_cost_usd=None,
            pricing_status="unknown",
            cache_read_tokens=0,
            cache_write_tokens=0,
        )
    )

    assert "Turn cost: n/a" in summary
    assert "pricing unknown for local/model" in summary
