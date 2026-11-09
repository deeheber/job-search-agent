import asyncio
from collections.abc import Iterator
from typing import Any
from unittest.mock import AsyncMock, Mock, call, patch

import pytest
from mcp.types import Tool
from strands import Agent
from strands.hooks import AfterToolCallEvent, BeforeToolCallEvent
from strands.tools.executors import SequentialToolExecutor
from strands.tools.mcp.mcp_agent_tool import MCPAgentTool

from src.agentcore_app import _tracked_job_search, get_agent
from tavily_retry import TavilyRetry


def rate_limited() -> dict[str, Any]:
    return {
        "toolUseId": "search",
        "status": "success",
        "content": [{"text": "Search failed: rate limited"}],
        "structuredContent": {"error": "Search failed", "status": 429},
        "isError": False,
    }


@pytest.fixture
def retry_agent(tavily_client: Mock) -> Iterator[Agent]:
    tavily_client.load_tools.return_value = [
        MCPAgentTool(Tool(name=name, inputSchema={"type": "object"}), tavily_client)
        for name in ("tavily_search", "tavily_extract")
    ]
    with (
        patch("src.agentcore_app.get_anthropic_api_key", return_value="test-key"),
        patch.dict("os.environ", {"SNS_TOPIC_ARN": ""}),
    ):
        agent = get_agent()
    yield agent
    agent.cleanup()


def test_delayed_retries_recover_through_real_tool_executor(
    retry_agent: Agent, tavily_client: Mock
) -> None:
    """A successful MCP envelope can contain a 429; wait before each retry."""
    order: list[str | float] = []
    success = {"toolUseId": "search", "status": "success", "content": [{"text": "jobs"}]}

    async def request(**_: Any) -> dict[str, Any]:
        order.append("request")
        return rate_limited() if order.count("request") < 3 else success

    async def wait(delay: float) -> None:
        order.append(delay)

    tavily_client.call_tool_async = AsyncMock(side_effect=request)
    with (
        patch("tavily_retry.asyncio.sleep", side_effect=wait),
        patch("tavily_retry.random.uniform", return_value=5) as jitter,
    ):
        result = retry_agent.tool.tavily_search(query="Stripe jobs")
    assert isinstance(retry_agent.tool_executor, SequentialToolExecutor)
    assert result == success
    assert order == ["request", 35, "request", 65, "request"]
    assert jitter.call_args_list == [call(0, 5), call(0, 5)]
    assert all(
        call.kwargs["arguments"] == {"query": "Stripe jobs"}
        for call in tavily_client.call_tool_async.call_args_list
    )


def test_exhaustion_blocks_new_tavily_calls_but_not_notifications(
    retry_agent: Agent, tavily_client: Mock
) -> None:
    success = {"toolUseId": "search", "status": "success", "content": [{"text": "jobs"}]}
    tavily_client.call_tool_async = AsyncMock(
        side_effect=[rate_limited(), success, rate_limited(), rate_limited()]
    )
    with patch("tavily_retry.asyncio.sleep", new_callable=AsyncMock) as sleep:
        assert retry_agent.tool.tavily_search(query="Stripe jobs") == success
        result = retry_agent.tool.tavily_extract(urls=["https://stripe.com/careers"])
        blocked = retry_agent.tool.tavily_search(query="Stripe Software Engineer")
    assert tavily_client.call_tool_async.await_count == 4
    assert sleep.await_count == 2
    assert result["status"] == blocked["status"] == "error"
    assert "search as incomplete" in blocked["content"][0]["text"]
    event = BeforeToolCallEvent(
        agent=retry_agent,
        selected_tool=None,
        invocation_state={},
        tool_use={"toolUseId": "notify", "name": "send_job_alert", "input": {}},
    )
    asyncio.run(retry_agent.hooks.invoke_callbacks_async(event))
    assert not event.cancel_tool


def test_authentication_errors_are_not_retried(retry_agent: Agent, tavily_client: Mock) -> None:
    error = rate_limited()
    error["structuredContent"] = {"error": "Unauthorized", "status": 401}
    tavily_client.call_tool_async = AsyncMock(return_value=error)
    with patch("tavily_retry.asyncio.sleep", new_callable=AsyncMock) as sleep:
        retry_agent.tool.tavily_search(query="Stripe jobs")
    tavily_client.call_tool_async.assert_awaited_once()
    sleep.assert_not_awaited()


def test_background_timeout_cancels_retry_wait_and_cleans_up() -> None:
    retry = TavilyRetry()
    event = AfterToolCallEvent(
        agent=Mock(),
        selected_tool=None,
        invocation_state={},
        result=rate_limited(),
        tool_use={"toolUseId": "search", "name": "tavily_search", "input": {}},
    )

    async def invoke(_: str) -> None:
        await retry.after_tool(event)

    agent = Mock(invoke_async=AsyncMock(side_effect=invoke))
    with (
        patch("src.agentcore_app.get_agent", return_value=agent),
        patch("src.agentcore_app.JOB_SEARCH_TIMEOUT_SECONDS", 0.5),
        patch("src.agentcore_app.send_failure_alert") as alert,
        patch("src.agentcore_app.app.complete_async_task") as complete,
    ):
        asyncio.run(_tracked_job_search(123, "Stripe", "", ""))
    assert retry.retries == 1
    assert not event.retry
    agent.cleanup.assert_called_once()
    alert.assert_called_once_with("Stripe")
    complete.assert_called_once_with(123)
