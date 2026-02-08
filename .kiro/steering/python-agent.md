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

**Main**: BedrockAgentCoreApp + @app.entrypoint
**Secrets**: SSM Parameter Store integration
**Tools**: Community tools from `strands_tools` (`http_request`, `current_time`, `tavily_search`, `use_aws`)
**Custom Tools**: Add in `src/tools/` directory

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
