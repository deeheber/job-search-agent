# Job Search Agent

## Conventions

- **Env vars**: all in `agent/.env`, loaded by the agent for local dev AND by CDK during deploy (`cdk/cdk.json` uses `--env-file-if-exists=../agent/.env`). There is no `cdk/.env`.
- **AgentCore regions**: not available everywhere; check the [AWS availability page](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-regions.html) before deploying. CI deploys to us-west-2. Not enforced in code.
