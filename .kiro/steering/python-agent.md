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
**Tools**: Currently using community tools (`http_request`, `current_time`)
**Future**: Custom job search tools in `tools/` directory when needed

## Job Search Patterns

**Agent**: `Agent(tools=[http_request, current_time])` - HTTP requests + timestamp data
**Response**: Return `{"status": "success/error", "response/error": "...", "search_criteria": {...}}` pattern
**Company Analysis**: Use `http_request` to fetch career pages, `current_time` for job posting dates

## Current Implementation

**HTTP-based Search**: Leveraging `http_request` tool for web scraping and API calls
**Timestamp Tracking**: Using `current_time` for job posting freshness and search timestamps
**Job Site Integration**: Direct HTTP requests to company career pages and job boards
**Data Parsing**: Agent processes HTML/JSON responses to extract job information
**Future Tools**: Will add custom tools for advanced job search features as needed

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

**Default Model**: `us.anthropic.claude-sonnet-4-5-20250929-v1:0` (see `DEFAULT_MODEL_ID` in `agentcore_app.py`)

```python
def get_model_id() -> str:
    return os.getenv("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID)
```
