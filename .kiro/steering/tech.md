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
cd cdk && npm install && npm run cdk:deploy
```

## Configuration

- **Model**: Set `BEDROCK_MODEL_ID` in `.env` (local) or CDK env vars (deploy)
- **Tavily API Key**: Set `TAVILY_API_KEY` in `.env` (local) or create SSM parameter `/job-search-agent/tavily-api-key` (AWS)
- **Email Notifications**: Set `NOTIFICATION_EMAIL` in `.env` before deploy (optional); `SNS_TOPIC_ARN` is auto-set by CDK
- **Scheduled Searches**: Set `SCHEDULES` in `.env` as a JSON array (optional); creates EventBridge schedules on deploy
- **Stack Name**: Set `STACK_NAME` in `.env` to deploy multiple stacks to the same account/region (default: `JobSearchAgentStack`)
- **Settings**: `agent/pyproject.toml` (line length: 100, Python 3.13)
- **Logging**: `LOG_LEVEL` env var (default: INFO)
