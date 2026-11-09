"""Tests for the agent."""

import asyncio
import os
import threading
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

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
    get_tavily_client,
    invoke,
    run_job_search,
)


def test_agent_has_tools(tavily_client: Mock) -> None:
    """Search tools are registered; timestamps no longer require a tool call."""
    with (
        patch("src.agentcore_app.get_anthropic_api_key", return_value="mock-anthropic-key"),
        patch.dict(os.environ, {"SNS_TOPIC_ARN": ""}),
    ):
        agent = get_agent()
    tool_names = agent.tool_names
    assert set(tool_names) == {"tavily_search", "tavily_extract"}
    agent.cleanup()


def test_get_model_default_is_anthropic() -> None:
    """With no env vars set, the provider defaults to the Anthropic API."""
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
    """ANTHROPIC_MODEL_ID overrides the default Anthropic model."""
    with (
        patch.dict(os.environ, {"ANTHROPIC_MODEL_ID": "claude-opus-5"}, clear=True),
        patch("src.agentcore_app.get_anthropic_api_key", return_value="mock-anthropic-key"),
    ):
        model = get_model()
    assert isinstance(model, AnthropicModel)
    assert model.get_config()["model_id"] == "claude-opus-5"


def test_get_model_bedrock_provider() -> None:
    """The bedrock provider yields a bare model ID; Strands builds the client itself."""
    with patch.dict(os.environ, {"MODEL_PROVIDER": "bedrock"}, clear=True):
        model = get_model()
    assert model == DEFAULT_BEDROCK_MODEL_ID


def test_get_model_bedrock_model_id_override() -> None:
    """BEDROCK_MODEL_ID overrides the default Bedrock model."""
    env = {"MODEL_PROVIDER": "bedrock", "BEDROCK_MODEL_ID": "custom-model-id"}
    with patch.dict(os.environ, env, clear=True):
        model = get_model()
    assert model == "custom-model-id"


def test_get_model_unknown_provider_raises() -> None:
    """An unsupported MODEL_PROVIDER fails fast instead of silently falling back."""
    with patch.dict(os.environ, {"MODEL_PROVIDER": "openai"}, clear=True):
        with pytest.raises(ValueError, match="Unsupported MODEL_PROVIDER"):
            get_model()


def test_construct_job_search_prompt_company_only() -> None:
    """A company on its own produces a bare search prompt."""
    result = construct_job_search_prompt("Google")
    assert result == "Find jobs at Google."


def test_construct_job_search_prompt_with_all_params() -> None:
    """Title and location filters are folded into the prompt text."""
    result = construct_job_search_prompt("Microsoft", title="Software Engineer", location="remote")
    assert result == "Find jobs at Microsoft. Focus on 'Software Engineer' roles in remote."


def test_agent_with_sns_has_notification_tool_and_instructions(tavily_client: Mock) -> None:
    with (
        patch("src.agentcore_app.get_anthropic_api_key", return_value="mock-anthropic-key"),
        patch.dict(os.environ, {"SNS_TOPIC_ARN": "arn:aws:sns:us-west-2:123456789012:test-topic"}),
    ):
        agent = get_agent()
    assert "send_job_alert" in agent.tool_names
    assert "send_job_alert" in agent.system_prompt
    assert "NOTIFICATION INSTRUCTIONS" in agent.system_prompt
    agent.cleanup()


def test_invoke_requires_company() -> None:
    """A missing company returns an error payload rather than raising."""
    result = asyncio.run(invoke({"title": "Engineer"}))
    assert result == {"status": "error", "error": "Company name is required"}


def test_invoke_default_returns_accepted_and_runs_search_in_background() -> None:
    """The default path acks immediately and runs the search as a background task."""
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
    """A background search that fails alerts via SNS, since no caller sees its result."""
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
    """The sync flag runs the search inline and returns its full result."""
    full_result = {"status": "success", "response": "**Hiring Status**: Yes"}
    mock_search = AsyncMock(return_value=full_result)

    with patch("src.agentcore_app.run_job_search", mock_search):
        result = asyncio.run(invoke({"company": "Stripe", "sync": True}))

    assert result == full_result
    mock_search.assert_awaited_once_with("Stripe", "", "")


@pytest.mark.parametrize("fails", [False, True])
def test_search_cleans_up_after_success_or_failure(fails: bool) -> None:
    agent = Mock(invoke_async=AsyncMock(return_value="No jobs found"))
    if fails:
        agent.invoke_async.side_effect = RuntimeError("provider unavailable")

    with patch("src.agentcore_app.get_agent", return_value=agent):
        result = asyncio.run(run_job_search("Example", "", ""))

    agent.invoke_async.assert_awaited_once()
    agent.cleanup.assert_called_once()
    if fails:
        assert result == {"status": "error", "error": "Internal processing error"}
    else:
        assert result["status"] == "success"
        assert result["response"] == "No jobs found"


def test_tavily_authentication_and_tool_allowlist() -> None:
    with (
        patch("src.agentcore_app.get_tavily_api_key", return_value="ssm-key"),
        patch("src.agentcore_app.MCPClient") as client,
        patch.dict(os.environ, {"TAVILY_API_KEY": "local-key"}),
    ):
        get_tavily_client()
        assert os.environ["TAVILY_API_KEY"] == "local-key"
    client.assert_called_once()
    config = client.call_args.kwargs
    assert config["url"] == "https://mcp.tavily.com/mcp/"
    assert config["headers"] == {"Authorization": "Bearer ssm-key"}
    assert set(config["tool_filters"]["allowed"]) == {"tavily_search", "tavily_extract"}


@pytest.mark.parametrize("missing_tools", [False, True])
def test_failed_agent_setup_closes_tavily_client(tavily_client: Mock, missing_tools: bool) -> None:
    if missing_tools:
        tavily_client.load_tools.return_value = tavily_client.load_tools.return_value[:1]
    else:
        tavily_client.load_tools.side_effect = RuntimeError("MCP authentication failed")
    message = "missing required search tools" if missing_tools else "MCP authentication failed"
    with patch("src.agentcore_app.get_anthropic_api_key", return_value="test-key"):
        with pytest.raises((ValueError, RuntimeError), match=message):
            get_agent()
    tavily_client.stop.assert_called_once_with(None, None, None)


def test_cancelled_setup_releases_agent_when_worker_finishes() -> None:
    started, release = threading.Event(), threading.Event()
    agent = Mock(invoke_async=AsyncMock())

    def create() -> Mock:
        started.set()
        assert release.wait(timeout=5)
        return agent

    async def scenario() -> None:
        with patch("src.agentcore_app.get_agent", side_effect=create):
            task = asyncio.create_task(run_job_search("Example", "", ""))
            try:
                assert await asyncio.to_thread(started.wait, 2)
                task.cancel()
                await asyncio.sleep(0)
            finally:
                release.set()
            with pytest.raises(asyncio.CancelledError):
                await task
        agent.invoke_async.assert_not_awaited()
        agent.cleanup.assert_called_once()

    asyncio.run(scenario())
