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

from strands_tools.current_time import current_time

assert datetime.fromisoformat(current_time()).tzinfo is not None
print("current_time: passed")
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
