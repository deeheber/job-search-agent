# Project Structure

## Repository Layout

```
strands-agent/
├── agent/              # Python agent implementation
│   ├── src/           # Source code
│   ├── tests/         # Test files
│   ├── .venv/         # Virtual environment (gitignored)
│   ├── .env.example   # Environment variable template
│   ├── pyproject.toml # Project config & dependencies
│   └── README.md      # Agent-specific documentation
├── cdk/                # TypeScript CDK infrastructure
│   ├── bin/           # CDK app entry point
│   ├── lib/           # Stack definitions
│   ├── test/          # CDK tests
│   ├── cdk.json       # CDK configuration
│   ├── package.json   # Node dependencies and scripts
│   └── README.md      # CDK-specific documentation
├── .github/
│   └── workflows/     # GitHub Actions CI/CD pipelines
│       ├── agent-ci.yml  # Python agent CI
│       └── cdk-ci.yml    # CDK infrastructure CI
├── .kiro/             # Kiro IDE configuration
│   └── steering/      # AI assistant guidance documents
└── README.md          # Root documentation
```

## Agent Directory (`agent/`)

### Source Code (`src/`)

- `agentcore_app.py` - Agent implementation (runs locally and in cloud)
- `tools/` - Custom tools directory
  - `__init__.py` - Tools module initialization and exports
  - `custom_tools.py` - Domain-specific custom tools (can add more tool files as needed)

### Tests (`tests/`)

- `test_agent.py` - Agent test suite
- `test_tools/` - Tools test directory (mirrors src/tools structure)
  - `test_custom_tools.py` - Tests for custom tools (add test files for additional tool modules)
- Test files should mirror source structure

### Configuration Files

- `pyproject.toml` - Single source of truth for dependencies, build config, tool settings, and Docker deployment
- `Dockerfile` - Container definition for AgentCore Runtime
- `.python-version` - Python version specification (3.13)
- `.env.example` - Template for environment variables (copy to `.env` for local config)
- `quality-check.sh` - Automated script to run all Python quality checks with auto-fixing (tests, type checking, linting, formatting)

## Code Patterns

**Agent:** `Agent` class from `strands`, tools via `tools` parameter, wrap execution in `if __name__ == "__main__"`

**AgentCore:** `BedrockAgentCoreApp`, `@app.entrypoint`, accepts `prompt`, returns `status`/`response`

**Tools:** `@tool` decorator, add to existing/new files, export in `__init__.py`, type hints required

**Logging:** `LOG_LEVEL` env var (default: INFO), format: `%(levelname)s | %(name)s | %(message)s`

## CDK Directory (`cdk/`)

**Key Files:**

- `lib/strands-agent-stack.ts` - AgentCore Runtime stack (ARM64, IAM, Docker build)
- `bin/cdk.ts` - App entry point
- `test/cdk.test.ts` - Stack tests with snapshot testing
- Config: `package.json`, `tsconfig.json`, `jest.config.ts`, `eslint.config.mjs`, `cdk.json`

### Tests (`test/`)

- `cdk.test.ts` - CDK stack tests (IAM, resources, security, snapshots)
- `__snapshots__/` - Jest snapshot files

**Current Implementation:**

- Uses CDK 2.1033.0 with aws-bedrock-agentcore-alpha ^2.230.0-alpha.0
- Node.js 24 runtime environment
- TypeScript ~5.9.3 with strict type checking

## CI/CD

- **agent-ci.yml** - Python testing (pytest, mypy, ruff, black)
- **cdk-ci.yml** - TypeScript testing (Jest, ESLint, Prettier)
- Runs on push/PR to main
