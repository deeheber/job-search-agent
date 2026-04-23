# CDK Infrastructure

The TypeScript side that deploys everything to AWS. This creates the AgentCore Runtime, IAM role, SNS topic for notifications, and (optionally) EventBridge schedules.

## Prerequisites

Get a Tavily API key at [tavily.com](https://tavily.com) (free tier available), then store it in SSM Parameter Store before deploying:

```bash
aws ssm put-parameter \
  --name "/job-search-agent/tavily-api-key" \
  --value "tvly-xxxxx" \
  --type SecureString
```

## Deploy

```bash
npm install
npm run cdk:deploy
```

Takes a few minutes. The stack builds a Docker image from `../agent`, pushes it to ECR, and creates an AgentCore Runtime on ARM64 (cheaper than x86).

## What Gets Created

- **AgentCore Runtime** - Serverless container that runs your agent
- **IAM Role** - Permissions for Bedrock models, SSM parameter read, KMS decrypt (for SSM), and SNS publish
- **ECR Repository** - Auto-created by the Docker asset to store the agent image
- **SNS Topic** - Receives hiring notifications; email subscriptions added when `NOTIFICATION_EMAILS` is set
- **EventBridge Schedules + SQS DLQ** _(optional)_ - Created when `SCHEDULES` is set, one schedule per entry

The stack outputs `RuntimeId`, `RuntimeArn`, `TavilyApiKeyParameter`, and `NotificationTopicArn`.

## Development

```bash
npm test              # Run tests with snapshots
npm run fix           # Auto-fix linting and formatting
npm run check         # CI validation (no changes)
npm run cdk:synth     # Generate CloudFormation template
npm run cdk:diff      # See what changed
```

Tests validate IAM permissions, resource properties, and security configurations. Snapshots catch unintended infrastructure changes.

## Stack Structure

The stack follows this pattern:

1. **IAM roles** - Set up permissions first
2. **Core resources** - AgentCore Runtime with Docker build
3. **Outputs** - Export RuntimeId, RuntimeArn, TavilyApiKeyParameter, and NotificationTopicArn

All imports are explicit (no wildcards), and we use TypeScript strict mode.

## Customization

Want to change the model? Set `BEDROCK_MODEL_ID` in `agent/.env`, then run `npm run cdk:deploy`.

## Next Steps

For complete deployment instructions, see [../DEPLOYMENT.md](../DEPLOYMENT.md).
