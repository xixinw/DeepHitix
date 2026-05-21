from __future__ import annotations

import inspect
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from agent.usage_pricing import CanonicalUsage
from run_agent import AIAgent


def _bare_agent() -> AIAgent:
    agent = AIAgent.__new__(AIAgent)
    agent.provider = "deepseek"
    agent.api_mode = "openai_chat"
    agent.model = "deepseek-chat"
    agent.session_id = "session-123"
    agent._api_call_count = 7
    agent._vprint = lambda *args, **kwargs: None
    agent.log_prefix = ""
    return agent


def test_agent_init_exposes_deepseek_routing_config_knobs():
    signature = inspect.signature(AIAgent.__init__)

    assert signature.parameters["deepseek_routing_enabled"].default is False
    assert signature.parameters["deepseek_flash_model"].default == "deepseek-v4-flash"
    assert signature.parameters["deepseek_pro_model"].default == "deepseek-v4-pro"


def _routing_agent() -> AIAgent:
    agent = _bare_agent()
    agent.deepseek_routing_enabled = True
    agent.deepseek_flash_model = "deepseek-v4-flash"
    agent.deepseek_pro_model = "deepseek-v4-pro"
    agent._one_shot_pro_pending = False
    return agent


def test_apply_turn_routing_explicit_pro_updates_model_and_safe_telemetry_metadata():
    agent = _routing_agent()

    routed_message = agent._apply_turn_routing("/pro analyze SECRET_PROMPT_BODY")

    assert routed_message == "analyze SECRET_PROMPT_BODY"
    assert agent.model == "deepseek-v4-pro"
    assert agent._last_routing_decision == "pro"
    assert agent._last_escalation_reason == "explicit_pro_command"
    assert agent._one_shot_pro_pending is False
    assert "SECRET_PROMPT_BODY" not in repr(
        {
            "routing_decision": agent._last_routing_decision,
            "escalation_reason": agent._last_escalation_reason,
        }
    )


def test_apply_turn_routing_next_normal_turn_returns_to_flash():
    agent = _routing_agent()
    agent._apply_turn_routing("/pro one turn only")

    routed_message = agent._apply_turn_routing("normal follow-up")

    assert routed_message == "normal follow-up"
    assert agent.model == "deepseek-v4-flash"
    assert agent._last_routing_decision == "flash"
    assert agent._last_escalation_reason is None

def test_emit_llm_call_telemetry_writes_one_safe_main_call_event():
    agent = _bare_agent()
    # These content-bearing attributes exist on the real agent, but must never
    # be copied into telemetry.
    agent.messages = [{"role": "user", "content": "secret prompt"}]
    agent._current_streamed_assistant_text = "assistant body"

    usage = CanonicalUsage(
        input_tokens=600,
        output_tokens=50,
        cache_read_tokens=400,
        cache_write_tokens=0,
        reasoning_tokens=12,
    )
    cost = SimpleNamespace(
        amount_usd=Decimal("0.00023"),
        status="estimated",
        source="official_docs_snapshot",
    )

    with patch("run_agent.append_telemetry_event", return_value=True) as append:
        assert agent._emit_llm_call_telemetry(usage, cost, 1.234, call_type="main") is True

    append.assert_called_once()
    event = append.call_args.args[0]
    assert event["event_type"] == "llm_call"
    assert event["provider"] == "deepseek"
    assert event["api_mode"] == "openai_chat"
    assert event["model"] == "deepseek-chat"
    assert event["call_type"] == "main"
    assert event["session_id"] == "session-123"
    assert event["turn_id"] == "7"
    assert event["prompt_tokens"] == 1000
    assert event["completion_tokens"] == 50
    assert event["total_tokens"] == 1050
    assert event["cache_read_tokens"] == 400
    assert event["cache_miss_tokens"] == 600
    assert event["reasoning_tokens"] == 12
    assert event["estimated_cost_usd"] == 0.00023
    assert event["pricing_status"] == "estimated"
    assert event["pricing_source"] == "official_docs_snapshot"
    assert event["latency_ms"] == 1234
    assert event["routing_decision"] == "unknown"
    assert event["escalation_reason"] is None
    forbidden = {"prompt", "messages", "assistant_message", "assistant_content", "content", "response", "raw_response"}
    assert forbidden.isdisjoint(event)
    assert "secret prompt" not in repr(event)
    assert "assistant body" not in repr(event)


def test_emit_llm_call_telemetry_includes_cache_observability_hashes_without_content():
    agent = _bare_agent()
    agent.tools = [
        {
            "type": "function",
            "function": {
                "name": "terminal",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "SECRET_TOOL_SCHEMA_TEXT"},
                    },
                },
            },
        }
    ]
    agent._last_api_messages = [
        {"role": "system", "content": "SECRET_SYSTEM_PREFIX"},
        {"role": "user", "content": "SECRET_USER_PROMPT"},
    ]
    usage = CanonicalUsage(input_tokens=10, output_tokens=2)
    cost = SimpleNamespace(amount_usd=None, status="unknown", source="none")

    with patch("run_agent.append_telemetry_event", return_value=True) as append:
        assert agent._emit_llm_call_telemetry(usage, cost, 0.01, call_type="main") is True

    event = append.call_args.args[0]
    assert event["tool_schema_hash"].startswith("sha256:")
    assert event["immutable_prefix_hash"].startswith("sha256:")
    assert "SECRET_TOOL_SCHEMA_TEXT" not in repr(event)
    assert "SECRET_SYSTEM_PREFIX" not in repr(event)
    assert "SECRET_USER_PROMPT" not in repr(event)


def test_emit_llm_call_telemetry_flags_prefix_drift_without_content():
    agent = _bare_agent()
    agent.tools = [{"type": "function", "function": {"name": "terminal", "parameters": {"type": "object"}}}]
    usage = CanonicalUsage(input_tokens=10, output_tokens=2)
    cost = SimpleNamespace(amount_usd=None, status="unknown", source="none")
    emitted = []

    def _capture(event):
        emitted.append(event)
        return True

    with patch("run_agent.append_telemetry_event", side_effect=_capture):
        agent._last_api_messages = [
            {"role": "system", "content": "STABLE_SYSTEM_PREFIX"},
            {"role": "user", "content": "first turn"},
        ]
        assert agent._emit_llm_call_telemetry(usage, cost, 0.01, call_type="main") is True

        agent._last_api_messages = [
            {"role": "system", "content": "CHANGED_SYSTEM_PREFIX_SECRET"},
            {"role": "user", "content": "second turn SECRET_PROMPT_BODY"},
        ]
        assert agent._emit_llm_call_telemetry(usage, cost, 0.01, call_type="main") is True

    assert emitted[0]["prefix_drift_reason"] is None
    assert emitted[1]["prefix_drift_reason"] == "immutable_prefix_changed"
    assert "CHANGED_SYSTEM_PREFIX_SECRET" not in repr(emitted[1])
    assert "SECRET_PROMPT_BODY" not in repr(emitted[1])


def test_emit_llm_call_telemetry_is_best_effort_on_writer_failure():
    agent = _bare_agent()
    usage = CanonicalUsage(input_tokens=1, output_tokens=2)
    cost = SimpleNamespace(amount_usd=None, status="unknown", source="none")

    with patch("run_agent.append_telemetry_event", side_effect=OSError("disk full")):
        assert agent._emit_llm_call_telemetry(usage, cost, 0.001) is False


def test_emit_llm_call_telemetry_prints_cli_turn_summary_only_for_cli():
    agent = _bare_agent()
    printed = []
    agent._vprint = lambda message, **kwargs: printed.append(message)
    agent.platform = "cli"
    usage = CanonicalUsage(input_tokens=600, output_tokens=50, cache_read_tokens=400)
    cost = SimpleNamespace(amount_usd=Decimal("0.00023"), status="estimated", source="official_docs_snapshot")

    with patch("run_agent.append_telemetry_event", return_value=True):
        assert agent._emit_llm_call_telemetry(usage, cost, 1.0) is True

    assert len(printed) == 1
    assert "Turn cost: ~$0.0002" in printed[0]
    assert "tokens 1,050" in printed[0]
    assert "cache 400/1,000" in printed[0]
    assert agent._last_llm_call_event["total_tokens"] == 1050

    printed.clear()
    agent.platform = "telegram"
    with patch("run_agent.append_telemetry_event", return_value=True):
        assert agent._emit_llm_call_telemetry(usage, cost, 1.0) is True
    assert printed == []
    assert agent._last_llm_call_event["cache_read_tokens"] == 400
