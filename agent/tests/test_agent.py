"""Tests for the agent."""

import asyncio
import os
from collections.abc import AsyncIterable
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from strands import Agent, tool
from strands.models import Model
from strands.models.anthropic import AnthropicModel
from strands.types.content import Messages, SystemContentBlock
from strands.types.streaming import StreamEvent
from strands.types.tools import ToolChoice, ToolSpec

from src.agentcore_app import (
    ANTHROPIC_MAX_TOKENS,
    DEFAULT_ANTHROPIC_MODEL_ID,
    DEFAULT_BEDROCK_MODEL_ID,
    PARALLEL_SEARCH_MCP_ENDPOINT,
    PARALLEL_SEARCH_PROVIDER,
    _background_tasks,
    construct_job_search_prompt,
    get_agent,
    get_model,
    invoke,
    run_job_search,
)


def test_agent_has_tools() -> None:
    """The search and timestamp tools are registered on every agent."""
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


def test_agent_with_sns_has_send_job_alert_tool() -> None:
    """send_job_alert is registered only when SNS_TOPIC_ARN is set."""
    with (
        patch("src.agentcore_app.get_tavily_api_key", return_value="mock-api-key"),
        patch("src.agentcore_app.get_anthropic_api_key", return_value="mock-anthropic-key"),
        patch.dict(os.environ, {"SNS_TOPIC_ARN": "arn:aws:sns:us-west-2:123456789012:test-topic"}),
    ):
        agent = get_agent()
    assert "send_job_alert" in agent.tool_names


def test_system_prompt_includes_sns_when_configured() -> None:
    """Notification instructions are appended to the system prompt when SNS is configured."""
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


class ToolCallingModel(Model):
    """Deterministic model that calls web_search once, then returns text."""

    def __init__(self, tool_input: dict[str, object]) -> None:
        self.tool_input = tool_input
        self.calls = 0

    def update_config(self, **model_config: Any) -> None:
        pass

    def get_config(self) -> dict[str, object]:
        return {}

    async def structured_output(self, *args: Any, **kwargs: Any) -> AsyncIterable[dict[str, Any]]:
        if False:
            yield {}
        raise NotImplementedError

    async def stream(
        self,
        messages: Messages,
        tool_specs: list[ToolSpec] | None = None,
        system_prompt: str | None = None,
        *,
        tool_choice: ToolChoice | None = None,
        system_prompt_content: list[SystemContentBlock] | None = None,
        invocation_state: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[StreamEvent]:
        self.calls += 1
        yield {"messageStart": {"role": "assistant"}}
        if self.calls == 1:
            yield {
                "contentBlockStart": {
                    "start": {"toolUse": {"toolUseId": "search-1", "name": "web_search"}}
                }
            }
            yield {
                "contentBlockDelta": {
                    "delta": {"toolUse": {"input": __import__("json").dumps(self.tool_input)}}
                }
            }
            yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "tool_use"}}
        else:
            yield {"contentBlockDelta": {"delta": {"text": "Parallel result used"}}}
            yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "end_turn"}}


class MockParallelClient:
    """MCP client double whose tool behaves like a connected hosted session."""

    def __init__(self, calls: list[dict[str, object]]) -> None:
        self.calls = calls
        self.active = False
        self.entered = False
        self.exited = False

    def __enter__(self) -> MockParallelClient:
        self.active = True
        self.entered = True
        return self

    def __exit__(self, *args: object) -> None:
        self.active = False
        self.exited = True

    def list_tools_sync(self) -> list[object]:
        client = self

        @tool
        def web_search(objective: str, search_queries: list[str]) -> dict[str, object]:
            """Search the public web using an objective and search queries."""
            assert client.active, "MCP session closed before the agent's tool call"
            call: dict[str, object] = {
                "objective": objective,
                "search_queries": search_queries,
            }
            client.calls.append(call)
            return {
                "results": [
                    {
                        "url": "https://example.com/jobs/1",
                        "title": "Engineer",
                        "excerpts": ["An open engineering position."],
                    },
                    {
                        "url": "https://example.com/jobs/2",
                        "excerpts": ["A second public position."],
                    },
                ]
            }

        return [web_search]


def test_parallel_opt_in_runs_real_agent_with_live_session_and_public_fields_only() -> None:
    """The MCP context spans the actual Strands agent's complete invocation."""
    calls: list[dict[str, object]] = []
    client = MockParallelClient(calls)
    tool_input: dict[str, object] = {
        "objective": "Find public Acme software engineer jobs in Remote",
        "search_queries": ["Acme software engineer jobs Remote"],
    }
    model = ToolCallingModel(tool_input)

    with (
        patch("src.agentcore_app.create_parallel_mcp_client", return_value=client),
        patch("src.agentcore_app.get_model", return_value=model),
        patch("src.agentcore_app.get_tavily_api_key", return_value="mock-tavily-key"),
    ):
        result = asyncio.run(
            run_job_search("Acme", "Software Engineer", "Remote", PARALLEL_SEARCH_PROVIDER)
        )

    assert result["status"] == "success"
    assert client.entered and client.exited and not client.active
    assert calls == [tool_input]
    serialized_calls = str(calls).lower()
    for private_value in (
        "resume text",
        "applicant profile",
        "person@example.com",
        "secret-token",
        "authorization",
    ):
        assert private_value not in serialized_calls
    assert set(calls[0]) == {"objective", "search_queries"}


def test_default_search_does_not_create_parallel_client() -> None:
    """Omitting search_provider retains Tavily and performs no Parallel setup or network work."""
    with (
        patch("src.agentcore_app.create_parallel_mcp_client") as create_client,
        patch("src.agentcore_app.get_tavily_api_key", return_value="mock-tavily-key"),
        patch("src.agentcore_app.get_anthropic_api_key", return_value="mock-anthropic-key"),
        patch.object(Agent, "invoke_async", new=AsyncMock(return_value="Tavily result")),
    ):
        result = asyncio.run(run_job_search("Acme", "Engineer", "Remote"))

    assert result["status"] == "success"
    create_client.assert_not_called()


def test_parallel_client_uses_canonical_anonymous_endpoint() -> None:
    """The opt-in client uses only the canonical endpoint, without headers or credentials."""
    transport_factory: object | None = None

    client_options: dict[str, object] = {}

    def capture_client(factory: object, **options: object) -> object:
        nonlocal transport_factory
        transport_factory = factory
        client_options.update(options)
        return object()

    with (
        patch("src.agentcore_app.MCPClient", side_effect=capture_client),
        patch("src.agentcore_app.streamablehttp_client") as transport,
    ):
        from src.agentcore_app import create_parallel_mcp_client

        create_parallel_mcp_client()
        assert callable(transport_factory)
        transport_factory()

    transport.assert_called_once_with(PARALLEL_SEARCH_MCP_ENDPOINT)
    assert client_options == {"tool_filters": {"allowed": ["web_search"]}}


def test_parallel_ignores_private_payload_fields() -> None:
    """Applicant fields never enter the sanitized company/title/location invocation."""
    search = AsyncMock(return_value={"status": "success"})
    payload = {
        "company": "Acme",
        "title": "Engineer",
        "location": "Remote",
        "search_provider": "parallel",
        "resume": "resume text",
        "email": "person@example.com",
        "authorization": "secret-token",
        "sync": True,
    }
    with patch("src.agentcore_app.run_job_search", search):
        asyncio.run(invoke(payload))

    search.assert_awaited_once_with("Acme", "Engineer", "Remote", "parallel")
