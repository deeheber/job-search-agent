# CDK Infrastructure

The TypeScript side that deploys everything to AWS. This creates the AgentCore Runtime, IAM roles, and CloudWatch logging.

## Deploy

```bash
npm install
npm run cdk:deploy
```

Takes about 5-10 minutes. The stack builds a Docker image from `../agent`, pushes it to ECR, and creates an AgentCore Runtime on ARM64 (cheaper than x86).

## What Gets Created

- **AgentCore Runtime** - Serverless container that runs your agent
- **IAM Role** - Permissions for Bedrock models, CloudWatch, and X-Ray
- **ECR Repository** - Stores the agent Docker image
- **CloudWatch Logs** - Agent execution logs and traces

The stack outputs `RuntimeId` and `RuntimeArn` for testing.

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
3. **Outputs** - Export RuntimeId and RuntimeArn

All imports are explicit (no wildcards), and we use TypeScript strict mode.

## Customization

Want to change the model or add environment variables? Edit `lib/job-search-agent-stack.ts`:

```typescript
const runtime = new AgentCoreRuntime(this, 'JobSearchAgent', {
  // ... existing config
  environmentVariables: {
    BEDROCK_MODEL_ID: 'your-model-id',
    CUSTOM_VAR: 'value',
  },
})
```

## Next Steps

For complete deployment instructions, see [../DEPLOYMENT.md](../DEPLOYMENT.md).
