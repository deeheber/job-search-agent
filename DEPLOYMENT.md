# Deployment Guide

Get the job search agent running on AWS in minutes.

## What You Need

- AWS CLI configured (`aws configure`)
- Docker running locally
- Node.js 24 and Python 3.13
- Bedrock model access in your AWS account
- Tavily API key (sign up at [tavily.com](https://tavily.com) - free tier available)

Check [Amazon Bedrock AgentCore regions](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-regions.html) to make sure AgentCore is available where you want to deploy.

## Try It Locally First

Always test before deploying. Set up your Tavily API key and start the agent:

```bash
cd agent
echo "TAVILY_API_KEY=tvly-xxxxx" > .env  # Add your Tavily API key
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python src/agentcore_app.py
```

In another terminal, send a test request:

```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"company": "Stripe", "title": "Engineer"}'
```

## Deploy to AWS

### 1. Store the Tavily API Key

The agent needs a Tavily API key for web search. Store it in SSM Parameter Store:

```bash
aws ssm put-parameter \
  --name "/job-search-agent/tavily-api-key" \
  --value "tvly-xxxxx" \
  --type SecureString
```

Get your API key at [tavily.com](https://tavily.com).

### 2. Set Up Email Notifications (Optional)

To receive email alerts when companies are hiring, add your email to `agent/.env`:

```bash
NOTIFICATION_EMAIL=your-email@example.com
```

After deploying, you'll receive a confirmation email — click the link to activate notifications.

### 3. Bootstrap and Deploy

First time only, bootstrap CDK:

```bash
cd cdk
cdk bootstrap
```

Then deploy:

```bash
npm install
npm run cdk:deploy
```

This takes a few minutes. CDK builds a Docker image, pushes it to ECR, and creates an AgentCore Runtime. When it finishes, you'll see outputs like:

```
JobSearchAgentStack.RuntimeId = job-search-agent-abc123
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
  --payload $(echo '{"company": "Netflix", "title": "Data Scientist"}' | base64) \
  response.json

cat response.json
```

Or use the AWS Console: Bedrock AgentCore → Runtimes → `JobSearchAgentStack_JobSearchAgent` → Test tab.

Try these payloads:

- `{"company": "Stripe"}`
- `{"company": "Netflix", "title": "Engineer", "location": "remote"}`
- `{"company": "Panic Inc.", "title": "Software Engineer"}`

## Check the Logs

See what the agent is doing:

```bash
# List log groups
aws logs describe-log-groups --log-group-name-prefix /aws/bedrock-agentcore/runtimes/JobSearchAgentStack

# Tail logs in real-time
aws logs tail /aws/bedrock-agentcore/runtimes/JobSearchAgentStack_JobSearchAgent-<id>-DEFAULT --follow
```

## Change the Model

Want to use a different Bedrock model? Edit `cdk/.env`:

```bash
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0
```

Then redeploy: `npm run cdk:deploy`

See [Amazon Bedrock Model IDs](https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html) for available models.

## Development Loop

1. Edit `agent/src/agentcore_app.py`
2. Run `cd agent && ./quality-check.sh` (auto-fixes most issues)
3. Test locally: `python src/agentcore_app.py`
4. Deploy: `cd cdk && npm run cdk:deploy`

The quality check runs mypy, ruff, black, and pytest. It'll catch most problems before deployment.

## Add Custom Tools

The agent uses community tools (`tavily_search`, `http_request`, `current_time`). To add your own:

```python
# agent/src/tools/job_search_tools.py
from strands.agent import tool

@tool
def parse_greenhouse_api(company_id: str) -> dict:
    """Fetch jobs from Greenhouse API."""
    # Your implementation
    return {"jobs": [...]}
```

Export it in `agent/src/tools/__init__.py`:

```python
from .job_search_tools import parse_greenhouse_api
__all__ = ["parse_greenhouse_api"]
```

Add to the agent in `agentcore_app.py`:

```python
from tools import parse_greenhouse_api
agent = Agent(tools=[current_time, http_request, tavily_search, parse_greenhouse_api])
```

## CI/CD with GitHub Actions

The repo includes GitHub Actions workflows for automated testing and deployment. To enable deployment:

1. Set up [OIDC authentication between GitHub and AWS](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws)
2. Add the IAM role ARN as a repository secret named `AWS_ROLE_TO_ASSUME`

Now every push to main runs tests and deploys automatically.

## What's Next

The agent currently does one-off lookups. Future enhancements:

- **Scheduled checks**: Use EventBridge to run searches periodically

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

**Runtime errors**: Check CloudWatch logs. The agent logs every request and tool call.

**Model access**: If you get "model not found" errors, enable the model in the Bedrock console first.
