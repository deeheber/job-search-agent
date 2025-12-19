---
inclusion: fileMatch
fileMatchPattern: "agent/**"
---

# Python Standards

## Configuration

**Python**: 3.13, pyproject.toml, 100 char line length
**Style**: Strict typing, Google docstrings, `strands_tools` imports
**Tools**: MyPy strict mode, Ruff (E,F,I,N,W,UP), Black, Pytest

## Structure

**Main**: `agentcore_app.py` (BedrockAgentCoreApp + @app.entrypoint)
**Tools**: `tools/custom_tools.py` (@tool decorator), export in `__init__.py`

## Patterns

**Agent**: `Agent(tools=[calculator, current_time, http_request, custom_tool])`
**Tool**: `@tool` decorator with Google docstrings (Args, Returns, Raises)
**Error**: Return `{"status": "success/error", "response/error": "..."}` pattern

## Commands

**Quality**: `./quality-check.sh` (all checks with auto-fix)
**Manual**: `pytest && mypy src/ && ruff check --fix . && black .`

## Testing

**Agent**: `assert "tool_name" in get_agent().tool_names`
**Functions**: Type hints required, descriptive docstrings

## Environment

**LOG_LEVEL**: INFO (default), DEBUG, ERROR
**BEDROCK_MODEL_ID**: Configure Bedrock model (see `DEFAULT_MODEL_ID` in `agentcore_app.py`)
**AWS regions**: Auto-set by AgentCore Runtime

## Model Selection

**Default Model**: See `DEFAULT_MODEL_ID` constant in `agentcore_app.py`

```python
def get_model_id() -> str:
    return os.getenv("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID)
```
