# Technology Stack & Development

## Stack

- **Python 3.13** + **Node.js 24**
- **strands-agents[otel]** (>=1.23.0) + **strands-agents-tools** (>=0.2.19)
- **bedrock-agentcore** (>=1.2.0) + **boto3** (>=1.42.32)
- **aws-opentelemetry-distro** (>=0.14.2)
- **CDK 2.236.0** + **aws-bedrock-agentcore-alpha** ~2.236.0-alpha.0

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
