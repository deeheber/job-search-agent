import asyncio
import json
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import Mock, patch

import httpx
import pytest
from anthropic import AsyncAnthropic

from src.agentcore_app import run_job_search


@pytest.fixture(autouse=True)
def local_environment(tavily_client: Mock) -> Iterator[None]:
    with patch.dict(
        "os.environ",
        {
            "TAVILY_API_KEY": "test-tavily-key",
            "ANTHROPIC_API_KEY": "test-anthropic-key",
            "AWS_DEFAULT_REGION": "us-west-2",
            "AWS_EC2_METADATA_DISABLED": "true",
        },
        clear=True,
    ):
        yield


def test_search_with_anthropic() -> None:
    """Parse a mocked HTTP stream through the real Anthropic SDK and agent."""
    events = [
        {
            "type": "message_start",
            "message": {
                "id": "test-message",
                "type": "message",
                "role": "assistant",
                "model": "test-model",
                "content": [],
                "stop_reason": None,
                "stop_sequence": None,
                "usage": {"input_tokens": 1, "output_tokens": 0},
            },
        },
        {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}},
        {
            "type": "content_block_delta",
            "index": 0,
            "delta": {"type": "text_delta", "text": "No jobs found"},
        },
        {"type": "content_block_stop", "index": 0},
        {
            "type": "message_delta",
            "delta": {"stop_reason": "end_turn", "stop_sequence": None},
            "usage": {"output_tokens": 1},
        },
        {"type": "message_stop"},
    ]
    body = "".join(f"event: {event['type']}\ndata: {json.dumps(event)}\n\n" for event in events)
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            text=body,
        )
    )

    async def search() -> dict[str, Any]:
        async with AsyncAnthropic(
            api_key="test-anthropic-key",
            http_client=httpx.AsyncClient(transport=transport),
        ) as client:
            with patch("anthropic.AsyncAnthropic", return_value=client):
                return await run_job_search("Example", "Engineer", "Remote")

    result = asyncio.run(search())

    assert result["status"] == "success"
    assert result["response"].strip() == "No jobs found"
    assert result["search_criteria"] == {
        "company": "Example",
        "title": "Engineer",
        "location": "Remote",
    }


def test_search_with_bedrock_refreshes_timestamp_after_tool_call() -> None:
    """The model gets current UTC context on both the initial and tool-result turns."""

    timestamps = [datetime(2026, 11, 8, 12, minute, tzinfo=UTC) for minute in (0, 1)]
    client = Mock()
    client.converse_stream.side_effect = [
        {
            "stream": [
                {"messageStart": {"role": "assistant"}},
                {
                    "contentBlockStart": {
                        "contentBlockIndex": 0,
                        "start": {
                            "toolUse": {"toolUseId": "search", "name": "tavily_search"},
                        },
                    }
                },
                {
                    "contentBlockDelta": {
                        "contentBlockIndex": 0,
                        "delta": {"toolUse": {"input": '{"query":"Example jobs"}'}},
                    }
                },
                {"contentBlockStop": {"contentBlockIndex": 0}},
                {"messageStop": {"stopReason": "tool_use"}},
            ]
        },
        {
            "stream": [
                {"messageStart": {"role": "assistant"}},
                {"contentBlockDelta": {"contentBlockIndex": 0, "delta": {"text": "No jobs found"}}},
                {"contentBlockStop": {"contentBlockIndex": 0}},
                {"messageStop": {"stopReason": "end_turn"}},
            ]
        },
    ]
    with (
        patch.dict("os.environ", {"MODEL_PROVIDER": "bedrock"}),
        patch("boto3.session.Session.client", return_value=client),
        patch("src.agentcore_app.datetime") as clock,
    ):
        clock.now.side_effect = timestamps
        result = asyncio.run(run_job_search("Example", "", ""))

    assert result["status"] == "success"
    assert result["response"].strip() == "No jobs found"
    messages = client.converse_stream.call_args.kwargs["messages"]
    tool_result = next(
        block["toolResult"] for block in messages[-1]["content"] if "toolResult" in block
    )
    assert tool_result["toolUseId"] == "search"
    assert tool_result["content"][0]["text"] == "No jobs found"
    for call, timestamp in zip(client.converse_stream.call_args_list, timestamps, strict=True):
        assert f"<current_time>{timestamp.isoformat()}</current_time>" in json.dumps(
            call.kwargs["messages"]
        )
