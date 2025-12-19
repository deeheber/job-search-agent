# CDK Infrastructure

Deploys Strands agents to Amazon Bedrock AgentCore Runtime.

## Deploy

```bash
npm install && npm run build && cdk deploy
```

Creates: AgentCore Runtime (ARM64), IAM role, CloudWatch logging.

## Development

```bash
npm test && npm run lint && npm run format
cdk synth  # Generate CloudFormation
```

See [DEPLOYMENT.md](../DEPLOYMENT.md) for complete instructions.
