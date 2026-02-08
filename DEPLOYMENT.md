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

The repo includes GitHub Actions workflows for automated testing and deployment. The `agent-ci.yml` workflow runs tests on every push and PR, while `cdk-ci.yml` handles testing and deployment to AWS.

### Required Repository Secrets

Set these secrets in your GitHub repository (Settings → Secrets and variables → Actions):

| Secret | Required | Description |
|--------|----------|-------------|
| `AWS_ROLE_TO_ASSUME` | Yes | ARN of the IAM role for OIDC authentication (e.g., `arn:aws:iam::123456789012:role/GitHubActionsRole`) |
| `AWS_REGION` | No | Currently hardcoded to `us-west-2` in the workflow. Modify `cdk-ci.yml` if you need a different region. |

### Create an IAM Role for GitHub OIDC Authentication

GitHub Actions uses OpenID Connect (OIDC) to authenticate with AWS without storing long-lived credentials. Follow these steps to create the required IAM role:

#### 1. Create the GitHub OIDC Identity Provider

First, add GitHub as an identity provider in your AWS account (only needed once per account):

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

Or in the AWS Console: IAM → Identity providers → Add provider → OpenID Connect:
- Provider URL: `https://token.actions.githubusercontent.com`
- Audience: `sts.amazonaws.com`

#### 2. Create the IAM Role

Create a role with a trust policy that allows GitHub Actions from your repository:

```bash
# Save the trust policy to a file
cat > trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_ORG/job-search-agent:*"
        }
      }
    }
  ]
}
EOF

# Create the role
aws iam create-role \
  --role-name GitHubActionsJobSearchAgent \
  --assume-role-policy-document file://trust-policy.json \
  --description "Role for GitHub Actions to deploy job-search-agent"
```

Replace `YOUR_ACCOUNT_ID` with your AWS account ID and `YOUR_GITHUB_ORG` with your GitHub username or organization.

#### 3. Attach Permissions to the Role

The role needs permissions to deploy CDK stacks. Attach the following managed policies:

```bash
# CDK bootstrap and CloudFormation permissions
aws iam attach-role-policy \
  --role-name GitHubActionsJobSearchAgent \
  --policy-arn arn:aws:iam::aws:policy/AWSCloudFormationFullAccess

# ECR permissions for pushing Docker images
aws iam attach-role-policy \
  --role-name GitHubActionsJobSearchAgent \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser

# SSM parameter access (for CDK synth validation)
aws iam attach-role-policy \
  --role-name GitHubActionsJobSearchAgent \
  --policy-arn arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess
```

For production, create a custom policy with least-privilege permissions instead of these broad managed policies.

#### 4. Add CDK Bootstrap Permissions

CDK requires additional permissions to assume the CDK execution roles. Add this inline policy:

```bash
cat > cdk-permissions.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::*:role/cdk-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:PassRole",
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:GetRole",
        "iam:TagRole"
      ],
      "Resource": "arn:aws:iam::*:role/JobSearchAgentStack-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sns:*"
      ],
      "Resource": "arn:aws:sns:*:*:JobSearchAgentStack-*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name GitHubActionsJobSearchAgent \
  --policy-name CDKDeployPermissions \
  --policy-document file://cdk-permissions.json
```

#### 5. Add the Secret to GitHub

Get the role ARN and add it as a repository secret:

```bash
# Get the role ARN
aws iam get-role --role-name GitHubActionsJobSearchAgent --query 'Role.Arn' --output text
```

In GitHub: Repository → Settings → Secrets and variables → Actions → New repository secret:
- Name: `AWS_ROLE_TO_ASSUME`
- Value: The role ARN from the command above (e.g., `arn:aws:iam::123456789012:role/GitHubActionsJobSearchAgent`)

### Optional Environment Variables

These environment variables can be set in the GitHub Actions workflow or passed during deployment:

| Variable | Default | Description |
|----------|---------|-------------|
| `BEDROCK_MODEL_ID` | `us.anthropic.claude-sonnet-4-20250514` | Override the default Bedrock model. See [Model IDs](https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html). |
| `NOTIFICATION_EMAIL` | _(none)_ | Email address for job search notifications. Must confirm subscription after first deploy. |
| `LOG_LEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `ERROR`). |

To add these to your GitHub Actions deployment, modify `.github/workflows/cdk-ci.yml`:

```yaml
- name: cdk deploy
  if: github.event_name == 'push' && github.ref == 'refs/heads/main'
  run: npm run cdk:deploy:ci
  env:
    LOG_LEVEL: INFO
    BEDROCK_MODEL_ID: us.anthropic.claude-sonnet-4-20250514  # Optional
    NOTIFICATION_EMAIL: alerts@example.com            # Optional
```

Or set them as GitHub Actions variables (Settings → Secrets and variables → Actions → Variables) and reference them as `${{ vars.VARIABLE_NAME }}`.

### How It Works

1. **On Pull Requests**: Both `agent-ci.yml` and `cdk-ci.yml` run tests, linting, and type checking
2. **On Push to Main**: Additionally, `cdk-ci.yml` deploys the stack to AWS using the OIDC role

The workflow authenticates using OIDC (no stored AWS credentials), synthesizes the CDK stack, and deploys only on pushes to main.

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
