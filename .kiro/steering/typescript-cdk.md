---
inclusion: fileMatch
fileMatchPattern: "cdk/**"
---

# TypeScript and CDK Standards

## Configuration

**TypeScript**: ES2023, NodeNext, strict mode, 100 char line length
**Tools**: ESLint + Prettier integration, type-aware linting

**Imports**: Explicit only, no wildcards

```typescript
// ✅ Good
import { Stack, StackProps } from "aws-cdk-lib";
// ❌ Avoid
import * as cdk from "aws-cdk-lib";
```

## Stack Patterns

**Structure**: IAM roles → AgentCore Runtime → Outputs
**Naming**: PascalCase construct IDs, underscore for runtime names
**Environment**: Auto-detect from AWS CLI

## IAM Security

**Required Permissions**: ECR (scoped to account), CloudWatch (bedrock-agentcore namespace), X-Ray, Bedrock models
**Pattern**: Use conditions and resource scoping, avoid wildcards where possible

## AgentCore Runtime

**Platform**: ARM64 for cost efficiency
**Artifact**: Docker build from `../../agent` directory
**Outputs**: RuntimeId and RuntimeArn

## Testing

**Categories**: IAM permissions, resources, security, snapshots
**Tools**: `Template.hasResourceProperties()`, `Match.arrayWith()`, `Match.stringLikeRegexp()`
**Security**: Validate least privilege, scoped resources, trust relationships

## Commands

**Development**: `npm run build`, `npm run test`, `npm run watch`
**Quality**: `npm run fix` (auto-fix), `npm run check` (CI validation)
**CDK**: `npm run cdk:deploy`, `npm run cdk:diff`, `npm run cdk:synth`

## Dependencies

**Core**: aws-cdk-lib, aws-bedrock-agentcore-alpha, constructs
**Dev**: TypeScript, ESLint, Prettier, Jest, aws-cdk CLI
**Regions**: us-west-2, us-east-1 (ensure AgentCore availability)

See `cdk/package.json` for current versions.
