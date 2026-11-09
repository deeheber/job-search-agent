#!/usr/bin/env bash
set -euo pipefail

agent_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
image="jsa-smoke:$$"
container="jsa-smoke-$$"

cleanup() {
    status=$?
    if (( status != 0 )); then
        docker logs "$container" >&2 || true
    fi
    docker rm -f "$container" >/dev/null 2>&1 || true
    docker image rm "$image" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker build --platform linux/arm64 -t "$image" "$agent_dir"
docker run -d --name "$container" --network none \
    -e OTEL_TRACES_EXPORTER=console \
    -e OTEL_METRICS_EXPORTER=none \
    -e OTEL_LOGS_EXPORTER=none \
    -e AWS_EC2_METADATA_DISABLED=true \
    "$image"

docker exec -i "$container" python - "$(cat "$agent_dir/.python-version")" <<'PY'
import json
import platform
import sys
import time
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from urllib.request import Request, urlopen

assert platform.python_version() == sys.argv[1], platform.python_version()
assert platform.machine() == "aarch64", platform.machine()
print(f"Python {platform.python_version()} on {platform.machine()}")

deadline = time.monotonic() + 60
while True:
    try:
        with urlopen("http://127.0.0.1:8080/ping", timeout=2) as response:
            assert json.load(response)["status"] == "Healthy"
        break
    except (OSError, ValueError, AssertionError):
        if time.monotonic() >= deadline:
            raise
        time.sleep(1)
print("/ping: Healthy")

request = Request(
    "http://127.0.0.1:8080/invocations",
    data=b'{"title":"x"}',
    headers={"Content-Type": "application/json"},
)
with urlopen(request, timeout=10) as response:
    assert json.load(response) == {"status": "error", "error": "Company name is required"}
print("/invocations: expected validation error")

import asyncio
import re

sys.path.insert(0, "/app/src")
from agentcore_app import get_agent
from strands import tool
from strands.tools.mcp import MCPClient

@tool(name="tavily_search")
def search(query: str) -> str:
    """Search for jobs."""
    return "No jobs found"

@tool(name="tavily_extract")
def extract(urls: list[str]) -> str:
    """Extract career page content."""
    return "No jobs found"

tavily = Mock(spec=MCPClient)
tavily.load_tools = AsyncMock(return_value=[search, extract])

client = Mock()
client.converse_stream.return_value = {"stream": [
    {"messageStart": {"role": "assistant"}},
    {"contentBlockDelta": {"contentBlockIndex": 0, "delta": {"text": "ok"}}},
    {"contentBlockStop": {"contentBlockIndex": 0}},
    {"messageStop": {"stopReason": "end_turn"}},
]}
with (
    patch("agentcore_app.get_tavily_client", return_value=tavily),
    patch("agentcore_app.get_model", return_value="test-model"),
    patch("boto3.session.Session.client", return_value=client),
):
    agent = get_agent()
    try:
        asyncio.run(agent.invoke_async("Check the timestamp"))
    finally:
        agent.cleanup()
messages = json.dumps(client.converse_stream.call_args.kwargs["messages"])
timestamp = re.search(r"<current_time>(.*?)</current_time>", messages).group(1)
assert datetime.fromisoformat(timestamp).utcoffset().total_seconds() == 0
assert "current_time" not in agent.tool_names
print("timestamp context: passed")
PY

for (( attempt=0; attempt<15; attempt++ )); do
    logs=$(docker logs "$container" 2>&1)
    if [[ "$logs" == *'"trace_id":'* ]]; then
        break
    fi
    sleep 1
done

if [[ "$logs" != *'"trace_id":'* ]]; then
    echo "No exported spans found" >&2
    exit 1
fi
if grep -Eq 'Traceback \(most recent call last\)|(^|[[:space:]])ERROR([[:space:]]|:)|Failed to auto initialize' <<< "$logs"; then
    echo "Container startup or instrumentation errors found" >&2
    exit 1
fi
echo "ARM64 container smoke test passed"
