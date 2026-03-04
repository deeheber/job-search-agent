# Job Search Agent

AI agent that finds hiring opportunities at companies using Tavily web search.

**Input**: Company name (+ optional title/location filters)
**Output**: Hiring status, matching positions, job links (+ optional SNS email alerts)

## Quick Reference

```bash
# Agent: cd agent && source .venv/bin/activate
python src/agentcore_app.py     # Run locally
./quality-check.sh              # All checks (auto-fix)

# CDK: cd cdk
npm run cdk:deploy              # Deploy
npm run fix                     # Auto-fix linting
```

## Key Files

- `agent/src/agentcore_app.py` - Agent implementation
- `agent/src/secret_utils.py` - SSM secrets integration
- `cdk/lib/job-search-agent-stack.ts` - Infrastructure

## Configuration

All env vars go in `agent/.env` (shared by agent local dev and CDK deploy):

- `BEDROCK_MODEL_ID` - Model to use
- `TAVILY_API_KEY` - For local dev; in AWS use SSM param `/job-search-agent/tavily-api-key`
- `NOTIFICATION_EMAILS` - Comma-separated, optional; creates SNS subscriptions on deploy
- `SCHEDULES` - JSON array, optional; creates EventBridge schedules on deploy
- `STACK_NAME` - Deploy multiple stacks to same account/region (default: `JobSearchAgentStack`)
- `LOG_LEVEL` - Default: INFO

## Conventions

- CDK imports: explicit only, no wildcards (`import { Stack } from "aws-cdk-lib"` not `import * as cdk`)
- AgentCore regions: us-west-2, us-east-1
