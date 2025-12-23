# Project Structure

## Key Directories

```
agent/                  # Python agent (src/, tests/, pyproject.toml)
cdk/                   # CDK infrastructure (lib/, bin/, test/)
.github/workflows/     # CI/CD (agent-ci.yml, cdk-ci.yml)
```

## Agent Files

- `src/agentcore_app.py` - Main agent implementation
- `src/tools/` - Custom tools (`__init__.py`, `custom_tools.py`)
- `tests/` - Test files (mirror src/ structure)
- `pyproject.toml` - Dependencies, build config, tool settings
- `Dockerfile` - AgentCore Runtime container
- `quality-check.sh` - Auto-fixing quality checks

## CDK Files

- `lib/strands-agent-stack.ts` - AgentCore Runtime stack
- `bin/cdk.ts` - App entry point
- `test/cdk.test.ts` - Stack tests with snapshots
