# Technology Stack & Development

## Stack

- **Python 3.13** + **Node.js 24**
- **Strands Agents** with OpenTelemetry + community tools
- **Bedrock AgentCore** + AWS SDK (boto3)
- **AWS CDK** with AgentCore alpha constructs

See `agent/pyproject.toml` and `cdk/package.json` for current versions.

## Quick Commands

**Agent Setup & Run:**

```bash
cd agent && python3.13 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
python src/agentcore_app.py     # Local run
./quality-check.sh              # All quality checks
```

**CDK Deploy:**

```bash
cd cdk && npm install && npm run build && cdk deploy
```

## Code Patterns

- **Agent**: `Agent` class, tools via `tools` parameter, `if __name__ == "__main__"`
- **AgentCore**: `BedrockAgentCoreApp`, `@app.entrypoint`, returns `status`/`response`
- **Tools**: `@tool` decorator, export in `__init__.py`, type hints required
- **CDK**: Explicit imports (avoid wildcards), TypeScript strict mode

## Configuration

- **Model**: Set `BEDROCK_MODEL_ID` in `.env` (local) or CDK env vars (deploy)
- **Settings**: `agent/pyproject.toml` (line length: 100, Python 3.13)
- **Logging**: `LOG_LEVEL` env var (default: INFO)
