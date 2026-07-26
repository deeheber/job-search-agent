"""Tests for the agent."""

import os
from unittest.mock import patch

import pytest
from strands.models.anthropic import AnthropicModel

from src.agentcore_app import (
    ANTHROPIC_MAX_TOKENS,
    DEFAULT_ANTHROPIC_MODEL_ID,
    DEFAULT_BEDROCK_MODEL_ID,
    construct_job_search_prompt,
    get_agent,
    get_model,
)


def test_agent_has_tools() -> None:
    """Test agent has expected tools registered."""
    with (
        patch("src.agentcore_app.get_tavily_api_key", return_value="mock-api-key"),
        patch("src.agentcore_app.get_anthropic_api_key", return_value="mock-anthropic-key"),
    ):
        agent = get_agent()
    tool_names = agent.tool_names
    assert "current_time" in tool_names
    assert "http_request" in tool_names
    assert "tavily_search" in tool_names


def test_get_model_default_is_anthropic() -> None:
    """Test get_model returns an AnthropicModel with defaults when env is unset."""
    with (
        patch.dict(os.environ, {}, clear=True),
        patch("src.agentcore_app.get_anthropic_api_key", return_value="mock-anthropic-key"),
    ):
        model = get_model()
    assert isinstance(model, AnthropicModel)
    config = model.get_config()
    assert config["model_id"] == DEFAULT_ANTHROPIC_MODEL_ID
    assert config["max_tokens"] == ANTHROPIC_MAX_TOKENS


def test_get_model_anthropic_model_id_override() -> None:
    """Test ANTHROPIC_MODEL_ID overrides the default Anthropic model."""
    with (
        patch.dict(os.environ, {"ANTHROPIC_MODEL_ID": "claude-opus-5"}, clear=True),
        patch("src.agentcore_app.get_anthropic_api_key", return_value="mock-anthropic-key"),
    ):
        model = get_model()
    assert isinstance(model, AnthropicModel)
    assert model.get_config()["model_id"] == "claude-opus-5"


def test_get_model_bedrock_provider() -> None:
    """Test MODEL_PROVIDER=bedrock returns the default Bedrock model ID string."""
    with patch.dict(os.environ, {"MODEL_PROVIDER": "bedrock"}, clear=True):
        model = get_model()
    assert model == DEFAULT_BEDROCK_MODEL_ID


def test_get_model_bedrock_model_id_override() -> None:
    """Test BEDROCK_MODEL_ID overrides the default Bedrock model."""
    env = {"MODEL_PROVIDER": "bedrock", "BEDROCK_MODEL_ID": "custom-model-id"}
    with patch.dict(os.environ, env, clear=True):
        model = get_model()
    assert model == "custom-model-id"


def test_get_model_unknown_provider_raises() -> None:
    """Test an unsupported MODEL_PROVIDER fails fast with a clear error."""
    with patch.dict(os.environ, {"MODEL_PROVIDER": "openai"}, clear=True):
        with pytest.raises(ValueError, match="Unsupported MODEL_PROVIDER"):
            get_model()


def test_system_prompt_contains_filtering_rules() -> None:
    """Test that system prompt contains strict filtering instructions."""
    from src.agentcore_app import SYSTEM_PROMPT

    # Check for key filtering concepts
    assert "Strict filtering" in SYSTEM_PROMPT
    assert "match ALL user criteria" in SYSTEM_PROMPT
    assert "NEVER construct or invent URLs" in SYSTEM_PROMPT
    assert "No direct link available" in SYSTEM_PROMPT

    # Check for specific role matching examples
    assert "Software Engineer" in SYSTEM_PROMPT
    assert "does NOT match" in SYSTEM_PROMPT


def test_construct_job_search_prompt_company_only() -> None:
    """Test prompt construction with company name only."""
    result = construct_job_search_prompt("Google")
    assert result == "Find jobs at Google."


def test_construct_job_search_prompt_with_all_params() -> None:
    """Test prompt construction with all parameters."""
    result = construct_job_search_prompt("Microsoft", title="Software Engineer", location="remote")
    assert result == "Find jobs at Microsoft. Focus on 'Software Engineer' roles in remote."


def test_system_prompt_uses_search_approach() -> None:
    """Test that system prompt uses tavily_search instead of URL guessing."""
    from src.agentcore_app import SYSTEM_PROMPT

    assert "tavily_search" in SYSTEM_PROMPT
    # Old URL patterns should be removed
    assert "https://careers.COMPANY.com" not in SYSTEM_PROMPT


def test_agent_with_sns_has_use_aws_tool() -> None:
    """Test agent includes use_aws tool when SNS_TOPIC_ARN is configured."""
    with (
        patch("src.agentcore_app.get_tavily_api_key", return_value="mock-api-key"),
        patch("src.agentcore_app.get_anthropic_api_key", return_value="mock-anthropic-key"),
        patch.dict(os.environ, {"SNS_TOPIC_ARN": "arn:aws:sns:us-west-2:123456789012:test-topic"}),
    ):
        agent = get_agent()
    assert "use_aws" in agent.tool_names


def test_system_prompt_includes_sns_when_configured() -> None:
    """Test system prompt contains SNS instructions with topic ARN when configured."""
    topic_arn = "arn:aws:sns:us-west-2:123456789012:test-topic"
    with (
        patch("src.agentcore_app.get_tavily_api_key", return_value="mock-api-key"),
        patch("src.agentcore_app.get_anthropic_api_key", return_value="mock-anthropic-key"),
        patch.dict(os.environ, {"SNS_TOPIC_ARN": topic_arn}),
    ):
        agent = get_agent()
    assert topic_arn in agent.system_prompt
    assert "sns" in agent.system_prompt.lower()
    assert "publish" in agent.system_prompt.lower()
