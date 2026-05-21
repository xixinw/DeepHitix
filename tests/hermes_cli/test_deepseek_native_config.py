from hermes_cli.config import DEFAULT_CONFIG


def test_deepseek_native_routing_defaults_are_safe_and_disabled():
    routing = DEFAULT_CONFIG["deepseek_native"]["routing"]

    assert routing["enabled"] is False
    assert routing["flash_model"] == "deepseek-v4-flash"
    assert routing["pro_model"] == "deepseek-v4-pro"
