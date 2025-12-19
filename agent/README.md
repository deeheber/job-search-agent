# Strands Agent

Python 3.13 agent with calculator, time, web search, and letter counter tools.

## Quick Start

```bash
python3.13 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
python src/agentcore_app.py
```

## Configuration

**Environment Variables**: The agent automatically loads environment variables from a `.env` file when running locally (requires `python-dotenv` from dev dependencies).

```bash
# Copy the example and customize
cp .env.example .env

# Edit .env file
BEDROCK_MODEL_ID=your-preferred-model-id
LOG_LEVEL=DEBUG
```

**Model**: Set `BEDROCK_MODEL_ID` environment variable (see `DEFAULT_MODEL_ID` in `src/agentcore_app.py` for current default)

**Available Models**: See [AWS Bedrock Model IDs documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html)

## Adding Tools

**Community Tools:**

```python
from strands_tools import http_request, file_read, browser
def get_agent() -> Agent:
    return Agent(tools=[calculator, current_time, http_request, browser])
```

**Custom Tools:**

```python
# In src/tools/my_tools.py
@tool
def my_tool(param: str) -> str:
    """Tool description."""
    return f"Result: {param}"

# Export in src/tools/__init__.py
from .my_tools import my_tool
__all__ = ["letter_counter", "my_tool"]
```

## Development

```bash
./quality-check.sh    # All quality checks (recommended)
pytest               # Tests only
```

See [DEPLOYMENT.md](../DEPLOYMENT.md) for cloud deployment.
