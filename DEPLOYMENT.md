# Deployment Guide

Get the job search agent running on AWS in minutes. Curious what it costs to run? See [COST.md](COST.md).

## What You Need

- AWS CLI configured (`aws configure`)
- Docker running locally
- Node.js 24 and Python 3.14
- [uv](https://docs.astral.sh/uv/) for Python package management
- Anthropic API key (sign up at [console.anthropic.com](https://console.anthropic.com)) — or Bedrock model access in your AWS account when using `MODEL_PROVIDER=bedrock`
- Tavily API key (sign up at [tavily.com](https://tavily.com) - free tier available)

Check [Amazon Bedrock AgentCore regions](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-regions.html) to make sure AgentCore is available where you want to deploy.

## Try It Locally First

Always test before deploying. Set up your API keys and start the agent:

```bash
cd agent
echo "ANTHROPIC_API_KEY=sk-ant-xxxxx" > .env
echo "TAVILY_API_KEY=tvly-xxxxx" >> .env
uv sync
uv run --env-file .env python src/agentcore_app.py
```

In another terminal, send a test request (`"sync": true` waits for the result; omit it for async):

```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"company": "Stripe", "title": "Engineer", "sync": true}'
```

## Deploy to AWS

### 1. Store the API Keys

The agent needs an Anthropic API key for the model (default provider) and a Tavily API key for web search. Store both in SSM Parameter Store:

```bash
aws ssm put-parameter \
  --name "/job-search-agent/anthropic-api-key" \
  --value "sk-ant-xxxxx" \
  --type SecureString

aws ssm put-parameter \
  --name "/job-search-agent/tavily-api-key" \
  --value "tvly-xxxxx" \
  --type SecureString
```

Get your keys at [console.anthropic.com](https://console.anthropic.com) and [tavily.com](https://tavily.com). The Anthropic parameter isn't needed if you deploy with `MODEL_PROVIDER=bedrock`.

### 2. Set Up Email Notifications (Optional)

To receive email alerts when companies are hiring, add emails to `agent/.env` (comma-separated for multiple):

```bash
NOTIFICATION_EMAILS=your-email@example.com,teammate@example.com
```

After deploying, each address will receive a confirmation email — click the link to activate notifications.

### 3. Bootstrap and Deploy

```bash
cd cdk
npm install
npx cdk bootstrap   # first deploy in this account/region only
npm run cdk:deploy
```

To deploy multiple stacks to the same account/region, set `STACK_NAME` in `agent/.env` (default: `JobSearchAgentStack`).

This takes a few minutes. CDK builds a Docker image, pushes it to ECR, and creates an AgentCore Runtime. When it finishes, you'll see outputs like:

```
JobSearchAgentStack.RuntimeId = JobSearchAgentStack_JobSearchAgent-abc123def4
JobSearchAgentStack.RuntimeArn = arn:aws:bedrock-agentcore:...
```

Save these for testing.

## Test on AWS

Use the AWS CLI with your RuntimeArn:

```bash
RUNTIME_ARN="arn:aws:bedrock-agentcore:us-west-2:123456789012:agent-runtime/..."

aws bedrock-agentcore invoke-agent-runtime \
  --agent-runtime-arn $RUNTIME_ARN \
  --qualifier DEFAULT \
  --payload $(echo '{"company": "Netflix", "title": "Data Scientist", "sync": true}' | base64) \
  response.json

cat response.json
```

Or use the AWS Console: Bedrock AgentCore → Runtimes → `JobSearchAgentStack_JobSearchAgent` → Test tab.

Try these payloads (keep `"sync": true` to see the result in the response; without it the agent returns `{"status": "accepted"}` and logs the result instead):

- `{"company": "Stripe", "sync": true}`
- `{"company": "Netflix", "title": "Engineer", "location": "remote", "sync": true}`
- `{"company": "Panic Inc.", "title": "Software Engineer", "sync": true}`

## Check the Logs

See what the agent is doing:

```bash
# List log groups
aws logs describe-log-groups --log-group-name-prefix /aws/bedrock-agentcore/runtimes/JobSearchAgentStack

# Tail logs in real-time
aws logs tail /aws/bedrock-agentcore/runtimes/JobSearchAgentStack_JobSearchAgent-<id>-DEFAULT --follow
```

## Change the Model or Provider

The agent supports two model providers, selected with `MODEL_PROVIDER` in `agent/.env`:

- **`anthropic`** (default) — calls the Anthropic API directly. Requires the Anthropic API key (SSM parameter above). Override the model with `ANTHROPIC_MODEL_ID` (default: `claude-sonnet-5`); see [Anthropic model IDs](https://docs.claude.com/en/docs/about-claude/models/overview).
- **`bedrock`** — uses Amazon Bedrock with the runtime's IAM role. Requires Bedrock model access in your account. Override the model with `BEDROCK_MODEL_ID` (default: `us.anthropic.claude-sonnet-5`); see [Amazon Bedrock model IDs](https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html).

```bash
MODEL_PROVIDER=bedrock
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-5
```

Then redeploy: `npm run cdk:deploy`

## Development Loop

1. Edit `agent/src/agentcore_app.py`
2. Run `cd agent && ./quality-check.sh` (auto-fixes most issues)
3. Test locally: `uv run --env-file .env python src/agentcore_app.py`
4. Deploy: `cd cdk && npm run cdk:deploy`

The quality check runs pytest, mypy, ruff, and black. It'll catch most problems before deployment.

## Add Custom Tools

The agent uses community tools (`tavily_search`, `tavily_extract`, `current_time`) plus a custom `send_job_alert` tool in `agent/src/tools/`. To add your own:

```python
# agent/src/tools/job_search_tools.py
from strands import tool

@tool
def parse_greenhouse_api(company_id: str) -> dict:
    """Fetch jobs from Greenhouse API."""
    # Your implementation
    return {"jobs": [...]}
```

Export it in `agent/src/tools/__init__.py`:

```python
from .job_search_tools import parse_greenhouse_api
from .sns_tools import send_failure_alert, send_job_alert

__all__ = ["parse_greenhouse_api", "send_failure_alert", "send_job_alert"]
```

Add it to the tool list in `get_agent()` in `agentcore_app.py`:

```python
from tools import parse_greenhouse_api

tools: list[object] = [current_time, tavily_search, tavily_extract, parse_greenhouse_api]
```

## CI/CD with GitHub Actions

The repo includes GitHub Actions workflows for automated testing and deployment. Every push to main runs tests, synth, and deploys to AWS automatically.

### Setup

1. Set up [OIDC authentication between GitHub and AWS](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws)
2. Add the IAM role ARN as a repository secret named `AWS_ROLE_TO_ASSUME`

### Optional Configuration

Set these as GitHub repository **variables** (Settings > Secrets and variables > Actions > Variables tab) to customize the deployment:

| Variable | Description | Default |
|---|---|---|
| `NOTIFICATION_EMAILS` | Comma-separated emails for SNS hiring alerts | _(none)_ |
| `SCHEDULES` | JSON array of scheduled searches (see [Scheduled Searches](#set-up-scheduled-searches-optional)) | _(none)_ |
| `MODEL_PROVIDER` | Model provider: `anthropic` or `bedrock` | `anthropic` |
| `ANTHROPIC_MODEL_ID` | Anthropic API model (when provider is `anthropic`) | `claude-sonnet-5` |
| `BEDROCK_MODEL_ID` | Bedrock model (when provider is `bedrock`) | `us.anthropic.claude-sonnet-5` |
| `STACK_NAME` | CloudFormation stack name | `JobSearchAgentStack` |

## Set Up Scheduled Searches (Optional)

Automate periodic job searches with EventBridge Scheduler. Add a `SCHEDULES` env var to `agent/.env` with a JSON array of companies to monitor:

```bash
SCHEDULES=[{"company":"Google","title":"Software Engineer","location":"Remote"},{"company":"Meta","schedule":"rate(14 days)"}]
```

Each entry creates an EventBridge schedule that invokes the agent automatically. Fields:

- **`company`** (required): Company name to search
- **`title`** (optional): Job title filter
- **`location`** (optional): Location filter
- **`schedule`** (optional): EventBridge expression — `cron(...)` or `rate(...)`. Defaults to `rate(7 days)`

Then redeploy:

```bash
cd cdk && npm run cdk:deploy
```

The agent sends SNS notifications when it finds open positions, so pair this with `NOTIFICATION_EMAILS` for automated alerts.

Scheduled invokes are async — the runtime acks immediately (EventBridge Scheduler's call times out after ~30s) and results arrive via SNS email or CloudWatch logs. Failed invokes land in an SQS dead-letter queue that alarms to the same SNS topic; failures inside the agent send their own SNS alert. To spread load, each schedule fires within a 2-hour window after its scheduled time, not at the exact minute.

## Clean Up

Done experimenting? Remove everything:

```bash
cd cdk && npm run cdk:destroy
```

This deletes the AgentCore Runtime and IAM roles. Note that CloudWatch logs and ECR images may persist and need manual cleanup if desired.

## Troubleshooting

**Docker not running**: Make sure `docker ps` works before deploying.

**Permission errors**: Your AWS user needs CloudFormation, ECR, IAM, and BedrockAgentCore permissions.

**Build failures**: Check the CDK output. Usually it's a missing dependency in `agent/pyproject.toml`.

**Runtime errors**: Check CloudWatch logs (see [Check the Logs](#check-the-logs)).

**Model access (anthropic provider)**: If invocations fail with an SSM `ParameterNotFound` error, create the `/job-search-agent/anthropic-api-key` parameter (see [Store the API Keys](#1-store-the-api-keys)). Authentication errors mean the stored key is invalid.

**Model access (bedrock provider)**: If you get "model not found" or throttling errors, enable the model in the Bedrock console and check your account's Bedrock quotas.
