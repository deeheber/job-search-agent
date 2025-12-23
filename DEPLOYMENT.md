# Deployment Guide

Deploy the job search agent to AWS Bedrock AgentCore Runtime for automated company hiring monitoring.

## Prerequisites

- AWS CLI configured (`aws configure`)
- Docker running
- Node.js 24, Python 3.13
- Bedrock model access enabled
- **For CI/CD**: GitHub Actions OIDC setup (see below)

**Supported regions**: See [AWS Bedrock AgentCore supported regions](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-regions.html) for current availability

## GitHub Actions CI/CD Setup

The CI/CD pipeline requires OIDC authentication to deploy from GitHub Actions to AWS. Follow the [GitHub documentation for configuring OIDC in AWS](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws), then add the role ARN as a repository secret named `AWS_ROLE_TO_ASSUME`.

## Configuration

**Model Selection** (optional): Set `BEDROCK_MODEL_ID` environment variable to use a different Bedrock model. If not provided, defaults to `us.anthropic.claude-sonnet-4-5-20250929-v1:0`.

```bash
# Local (agent/.env file)
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0

# CDK deployment (cdk/.env)
BEDROCK_MODEL_ID=us.amazon.titan-text-express-v1
```

## Local Testing

```bash
cd agent && source .venv/bin/activate && pip install -e ".[dev]"
python src/agentcore_app.py

# Test in another terminal
curl -X POST http://localhost:8080/invocations -H "Content-Type: application/json" -d '{"prompt": "What is 42 * 137?"}'
```

## Deploy

```bash
cd cdk && cdk bootstrap  # First time only
npm install && npm run build && cdk deploy
```

**Duration**: 5-10 minutes. Creates AgentCore Runtime, ECR image, IAM roles.

**Outputs**: Note `RuntimeId` and `RuntimeArn` for testing.

## Testing

**AWS CLI:**

```bash
RUNTIME_ARN="<your-runtime-arn>"
aws bedrock-agentcore invoke-agent-runtime --agent-runtime-arn $RUNTIME_ARN --qualifier DEFAULT --payload $(echo '{"prompt": "What is 42 * 137?"}' | base64) response.json
```

**AWS Console:** Bedrock AgentCore → Runtimes → `JobSearchAgentStack_JobSearchAgent` → Test

**Sample queries:**

- `"Is Panic Inc. hiring software engineers now?"`
- `"What positions are available at GitHub?"`
- `"Check if Stripe has any open engineering roles"`
- `"What is the time right now?"` (for testing)

## Monitoring

**CloudWatch Logs:**

```bash
aws logs describe-log-groups --log-group-name-prefix /aws/bedrock-agentcore/runtimes/JobSearchAgentStack
aws logs tail /aws/bedrock-agentcore/runtimes/JobSearchAgentStack_JobSearchAgent-<id>-DEFAULT --follow
```

## Development Workflow

1. **Edit** `agent/src/agentcore_app.py` for job search logic improvements
2. **Quality check** `cd agent && ./quality-check.sh`
3. **Test locally** `python src/agentcore_app.py` with job search queries
4. **Deploy** `cd cdk && npm run build && cdk deploy`

**Future Enhancements:**

- **Multi-company search**: Process multiple companies in one request
- **Scheduled monitoring**: EventBridge integration for periodic checks
- **Email alerts**: SNS notifications when hiring opportunities are found

**Adding Custom Tools:**

```python
# Future custom tool in src/tools/job_search_tools.py
@tool
def parse_job_board(url: str) -> dict:
    """Parse job board API for structured job data."""
    return {"jobs": [...]}

# Export in src/tools/__init__.py
from .job_search_tools import parse_job_board
__all__ = ["parse_job_board"]

# Community tools (currently used)
from strands_tools import http_request, current_time
```

## Cleanup

```bash
cd cdk && cdk destroy
```

Removes: AgentCore Runtime, ECR repository, IAM roles, CloudWatch logs.

## Troubleshooting

- **Docker issues**: Ensure `docker ps` works
- **Permissions**: Need CloudFormation, ECR, IAM, BedrockAgentCore access
- **Build failures**: Check CDK output, verify `pyproject.toml` dependencies
- **Runtime errors**: Check CloudWatch logs
