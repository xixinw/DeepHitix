"""DeepSeek-native runtime propagation for auxiliary side tasks."""

from unittest.mock import patch


def test_deepseek_routing_flags_reach_default_context_compressor():
    """AIAgent must pass DeepSeek routing metadata into compression runtime."""
    cfg = {"agent": {}, "compression": {"enabled": True}}

    with (
        patch("hermes_cli.config.load_config", return_value=cfg),
        patch("agent.context_compressor.get_model_context_length", return_value=131_072),
        patch("agent.model_metadata.get_model_context_length", return_value=131_072),
        patch("run_agent.get_tool_definitions", return_value=[]),
        patch("run_agent.check_toolset_requirements", return_value={}),
        patch("run_agent.OpenAI"),
    ):
        from run_agent import AIAgent

        agent = AIAgent(
            model="deepseek-v4-pro",
            provider="deepseek",
            api_key="test-key-1234567890",
            base_url="https://api.deepseek.com/v1",
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
            deepseek_routing_enabled=True,
            deepseek_flash_model="deepseek-v4-flash",
            deepseek_pro_model="deepseek-v4-pro",
        )

    compressor = agent.context_compressor
    assert compressor.deepseek_routing_enabled is True
    assert compressor.deepseek_flash_model == "deepseek-v4-flash"
    assert compressor.deepseek_pro_model == "deepseek-v4-pro"
