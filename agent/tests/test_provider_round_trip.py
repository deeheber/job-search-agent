import asyncio
import json
from collections.abc import Iterator
from datetime import datetime
from typing import Any
from unittest.mock import Mock, patch

import httpx
import pytest
from anthropic import AsyncAnthropic

from src.agentcore_app import run_job_search


@pytest.fixture(autouse=True)
def local_environment() -> Iterator[None]:
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


def test_search_with_bedrock_executes_time_tool() -> None:
    client = Mock()
    client.converse_stream.side_effect = [
        {
            "stream": [
                {"messageStart": {"role": "assistant"}},
                {
                    "contentBlockStart": {
                        "contentBlockIndex": 0,
                        "start": {
                            "toolUse": {"toolUseId": "clock", "name": "current_time"},
                        },
                    }
                },
                {
                    "contentBlockDelta": {
                        "contentBlockIndex": 0,
                        "delta": {"toolUse": {"input": "{}"}},
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
    ):
        result = asyncio.run(run_job_search("Example", "", ""))

    assert result["status"] == "success"
    assert result["response"].strip() == "No jobs found"
    messages = client.converse_stream.call_args.kwargs["messages"]
    tool_result = messages[-1]["content"][0]["toolResult"]
    assert tool_result["toolUseId"] == "clock"
    assert datetime.fromisoformat(tool_result["content"][0]["text"]).tzinfo is not None
