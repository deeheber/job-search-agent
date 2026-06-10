# Tasks: Migrate AgentCore to Stable Module

## Tasks

- [ ] 1. Update dependency and import
  - [ ] 1.1 Remove `@aws-cdk/aws-bedrock-agentcore-alpha` from `cdk/package.json` dependencies
  - [ ] 1.2 Change import in `cdk/lib/job-search-agent-stack.ts` from `'@aws-cdk/aws-bedrock-agentcore-alpha'` → `'aws-cdk-lib/aws-bedrockagentcore'`

- [ ] 2. Regenerate lock file
  - [ ] 2.1 Run `npm install` in `cdk/`

- [ ] 3. Regenerate snapshot and run tests
  - [ ] 3.1 Delete `cdk/test/__snapshots__/cdk.test.ts.snap`
  - [ ] 3.2 Run `npx vitest run` in `cdk/` — all tests should pass

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["3.1"] },
    { "id": 3, "tasks": ["3.2"] }
  ]
}
```
