---
inclusion: fileMatch
fileMatchPattern: "agent/**"
---

# Python Standards

## Configuration

**Python**: 3.13, pyproject.toml, 100 char line length
**Style**: Strict typing, Google docstrings
**Tools**: MyPy strict mode, Ruff (E,F,I,N,W,UP), Black, Pytest
**Dependencies**: See `agent/pyproject.toml` for current versions

## Structure

**Main**: `agentcore_app.py` (BedrockAgentCoreApp + @app.entrypoint)
**Secrets**: `secret_utils.py` (SSM Parameter Store integration for API keys)
**Tools**: Community tools from `strands_tools` package (`http_request`, `current_time`, `tavily_search`)
**Custom Tools**: Add in `src/tools/` directory when needed

## Agent Patterns

**Agent Creation**: `Agent(model=model_id, tools=[...], system_prompt=SYSTEM_PROMPT)`
**Response Format**: Return `{"status": "success/error", "response/error": "...", "search_criteria": {...}}`
**Tool Imports**: `from strands_tools import current_time, http_request` and `from strands_tools.tavily import tavily_search`

## Commands

**Quality**: `./quality-check.sh` (all checks with auto-fix)
**Manual**: `pytest && mypy src/ && ruff check --fix . && black .`

## Testing

**Agent**: Test tool availability with `assert "tool_name" in get_agent().tool_names`
**Functions**: Type hints required, descriptive docstrings

## Environment Variables

**LOG_LEVEL**: INFO (default), DEBUG, ERROR
**BEDROCK_MODEL_ID**: Override default model (see `DEFAULT_MODEL_ID` in `agentcore_app.py`)
**AWS_REGION**: Auto-set by AgentCore Runtime
**TAVILY_API_KEY**: Local dev only - Tavily API key (or use SSM)
**TAVILY_API_KEY_SSM_PARAMETER**: SSM parameter path (default: `/job-search-agent/tavily-api-key`)
