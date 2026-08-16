# CDK Infrastructure

The TypeScript side that deploys everything to AWS. This creates the AgentCore Runtime, IAM role, SNS topic for notifications, and (optionally) EventBridge schedules.

## Prerequisites

The stack reads the Anthropic and Tavily API keys from SSM Parameter Store, so store them before deploying: see [Store the API Keys](../DEPLOYMENT.md#1-store-the-api-keys). The Anthropic parameter isn't needed when deploying with `MODEL_PROVIDER=bedrock`.

## Deploy

```bash
npm install
npx cdk bootstrap   # first deploy in this account/region only
npm run cdk:deploy
```

Takes a few minutes. The stack builds a Docker image from `../agent`, pushes it to ECR, and creates an AgentCore Runtime on ARM64 (cheaper than x86).

## What Gets Created

- **AgentCore Runtime** - Serverless container that runs your agent
- **IAM Role** - Permissions for Bedrock models, SSM parameter reads (Tavily + Anthropic API keys), KMS decrypt (for SSM), and SNS publish
- **ECR Image** - The agent image is pushed to the shared ECR repository that `cdk bootstrap` manages (the stack doesn't create its own repository)
- **SNS Topic** - Receives hiring notifications; email subscriptions added when `NOTIFICATION_EMAILS` is set
- **EventBridge Schedules + SQS DLQ** _(optional)_ - Created when `SCHEDULES` is set, one schedule per entry, with a CloudWatch alarm that notifies the SNS topic when invokes go to the DLQ

The stack outputs `RuntimeId`, `RuntimeArn`, `TavilyApiKeyParameter`, `AnthropicApiKeyParameter`, and `NotificationTopicArn`.

## Development

```bash
npm test              # Run tests with snapshots
npm run fix           # Auto-fix linting and formatting
npm run check         # CI validation (no changes)
npm run cdk:synth     # Generate CloudFormation template
npm run cdk:diff      # See what changed
```

Tests validate IAM permissions, resource properties, and security configurations. Snapshots catch unintended infrastructure changes.

## Customization

Want to change the model or provider? Set `MODEL_PROVIDER` (`anthropic` default, or `bedrock`) and optionally `ANTHROPIC_MODEL_ID` / `BEDROCK_MODEL_ID` in `agent/.env`, then run `npm run cdk:deploy`.

## Next Steps

For complete deployment instructions, see [../DEPLOYMENT.md](../DEPLOYMENT.md).
