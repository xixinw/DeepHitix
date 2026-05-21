from agent.routing_policy import RoutingPolicyConfig, resolve_turn_routing


def test_default_turn_routes_to_flash_model():
    decision = resolve_turn_routing(
        "summarize this file",
        RoutingPolicyConfig(
            enabled=True,
            flash_model="deepseek-v4-flash",
            pro_model="deepseek-v4-pro",
        ),
    )

    assert decision.model == "deepseek-v4-flash"
    assert decision.routing_decision == "flash"
    assert decision.escalation_reason is None
    assert decision.consume_one_shot_pro is False


def test_explicit_pro_prefix_routes_one_turn_to_pro_and_sanitizes_reason():
    decision = resolve_turn_routing(
        "/pro 请认真分析我的商业计划原文 SECRET_CONTENT",
        RoutingPolicyConfig(
            enabled=True,
            flash_model="deepseek-v4-flash",
            pro_model="deepseek-v4-pro",
        ),
    )

    assert decision.model == "deepseek-v4-pro"
    assert decision.routing_decision == "pro"
    assert decision.escalation_reason == "explicit_pro_command"
    assert "SECRET_CONTENT" not in repr(decision)
    assert decision.sanitized_message == "请认真分析我的商业计划原文 SECRET_CONTENT"
    assert decision.consume_one_shot_pro is True


def test_one_shot_pro_state_routes_current_turn_to_pro_then_consumes_flag():
    decision = resolve_turn_routing(
        "next turn only",
        RoutingPolicyConfig(
            enabled=True,
            flash_model="deepseek-v4-flash",
            pro_model="deepseek-v4-pro",
        ),
        one_shot_pro_pending=True,
    )

    assert decision.model == "deepseek-v4-pro"
    assert decision.routing_decision == "pro"
    assert decision.escalation_reason == "one_shot_pro_pending"
    assert decision.consume_one_shot_pro is True
    assert decision.sanitized_message == "next turn only"


def test_disabled_policy_keeps_current_model_unknown_routing():
    decision = resolve_turn_routing(
        "/pro still no routing when disabled",
        RoutingPolicyConfig(
            enabled=False,
            flash_model="deepseek-v4-flash",
            pro_model="deepseek-v4-pro",
            current_model="deepseek-chat",
        ),
    )

    assert decision.model == "deepseek-chat"
    assert decision.routing_decision == "unknown"
    assert decision.escalation_reason is None
    assert decision.sanitized_message == "/pro still no routing when disabled"
