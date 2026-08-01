"""Tests for the agent."""

import asyncio
import os
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from strands.models.anthropic import AnthropicModel

from src.agentcore_app import (
    ANTHROPIC_MAX_TOKENS,
    DEFAULT_ANTHROPIC_MODEL_ID,
    DEFAULT_BEDROCK_MODEL_ID,
    _background_tasks,
    construct_job_search_prompt,
    get_agent,
    get_model,
    invoke,
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
    assert "tavily_search" in tool_names
    assert "tavily_extract" in tool_names


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


def test_construct_job_search_prompt_company_only() -> None:
    """Test prompt construction with company name only."""
    result = construct_job_search_prompt("Google")
    assert result == "Find jobs at Google."


def test_construct_job_search_prompt_with_all_params() -> None:
    """Test prompt construction with all parameters."""
    result = construct_job_search_prompt("Microsoft", title="Software Engineer", location="remote")
    assert result == "Find jobs at Microsoft. Focus on 'Software Engineer' roles in remote."


def test_agent_with_sns_has_send_job_alert_tool() -> None:
    """Test agent includes send_job_alert tool when SNS_TOPIC_ARN is configured."""
    with (
        patch("src.agentcore_app.get_tavily_api_key", return_value="mock-api-key"),
        patch("src.agentcore_app.get_anthropic_api_key", return_value="mock-anthropic-key"),
        patch.dict(os.environ, {"SNS_TOPIC_ARN": "arn:aws:sns:us-west-2:123456789012:test-topic"}),
    ):
        agent = get_agent()
    assert "send_job_alert" in agent.tool_names


def test_system_prompt_includes_sns_when_configured() -> None:
    """Test system prompt contains notification instructions when SNS is configured."""
    topic_arn = "arn:aws:sns:us-west-2:123456789012:test-topic"
    with (
        patch("src.agentcore_app.get_tavily_api_key", return_value="mock-api-key"),
        patch("src.agentcore_app.get_anthropic_api_key", return_value="mock-anthropic-key"),
        patch.dict(os.environ, {"SNS_TOPIC_ARN": topic_arn}),
    ):
        agent = get_agent()
    assert "send_job_alert" in agent.system_prompt
    assert "NOTIFICATION INSTRUCTIONS" in agent.system_prompt


def test_invoke_requires_company() -> None:
    """Test invoke returns an error when company is missing."""
    result = asyncio.run(invoke({"title": "Engineer"}))
    assert result == {"status": "error", "error": "Company name is required"}


def test_invoke_default_returns_accepted_and_runs_search_in_background() -> None:
    """Test the default path responds immediately and runs the search as a background task."""
    mock_search = AsyncMock(return_value={"status": "success"})

    async def scenario() -> dict[str, Any]:
        with patch("src.agentcore_app.run_job_search", mock_search):
            result = await invoke({"company": "Stripe", "title": "Engineer"})
            await asyncio.gather(*_background_tasks)
        return result

    result = asyncio.run(scenario())
    assert result["status"] == "accepted"
    mock_search.assert_awaited_once_with("Stripe", "Engineer", "")


def test_invoke_background_failure_sends_alert() -> None:
    """Test a failed background search publishes a failure alert."""
    mock_search = AsyncMock(return_value={"status": "error", "error": "Internal processing error"})

    async def scenario() -> None:
        with (
            patch("src.agentcore_app.run_job_search", mock_search),
            patch("src.agentcore_app.send_failure_alert") as mock_alert,
        ):
            await invoke({"company": "Stripe"})
            await asyncio.gather(*_background_tasks)
            mock_alert.assert_called_once_with("Stripe")

    asyncio.run(scenario())


def test_invoke_sync_returns_full_result() -> None:
    """Test the sync flag runs the search inline and returns its result."""
    full_result = {"status": "success", "response": "**Hiring Status**: Yes"}
    mock_search = AsyncMock(return_value=full_result)

    with patch("src.agentcore_app.run_job_search", mock_search):
        result = asyncio.run(invoke({"company": "Stripe", "sync": True}))

    assert result == full_result
    mock_search.assert_awaited_once_with("Stripe", "", "")
