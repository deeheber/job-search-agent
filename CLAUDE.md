# Job Search Agent

## Conventions

- **Env vars**: all in `agent/.env` — loaded by the agent for local dev AND by CDK during deploy (`cdk/cdk.json` uses `--env-file-if-exists=../agent/.env`). There is no `cdk/.env`.
- **CDK imports**: explicit only, no wildcards — e.g. `import { Stack } from "aws-cdk-lib"`, not `import * as cdk`.
- **AgentCore regions**: us-west-2 and us-east-1 (AWS availability constraint — not enforced in code).
