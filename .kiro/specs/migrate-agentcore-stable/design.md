# Design Document

## Overview

Migrate the CDK stack from `@aws-cdk/aws-bedrock-agentcore-alpha` to `aws-cdk-lib/aws-bedrockagentcore`. This is a straightforward dependency swap — the stable module (bundled in `aws-cdk-lib` 2.257.0+) exposes the same `Runtime` and `AgentRuntimeArtifact` classes with identical APIs. No code logic changes are needed.

## Changes

### 1. `cdk/package.json`

Remove `@aws-cdk/aws-bedrock-agentcore-alpha` from `dependencies`. No new package needed — `aws-cdk-lib` already includes the stable submodule.

### 2. `cdk/lib/job-search-agent-stack.ts`

Update the import line:

```typescript
// Before
import { Runtime, AgentRuntimeArtifact } from '@aws-cdk/aws-bedrock-agentcore-alpha'

// After
import { Runtime, AgentRuntimeArtifact } from 'aws-cdk-lib/aws-bedrockagentcore'
```

All construct usage stays the same — `runtimeName`, `agentRuntimeArtifact`, `executionRole`, `description`, `environmentVariables`, `.agentRuntimeArn`, `.agentRuntimeId` are identical in both modules.

### 3. `cdk/package-lock.json`

Regenerate via `npm install` after removing the alpha dependency.

### 4. `cdk/test/__snapshots__/cdk.test.ts.snap`

Delete and regenerate by running `vitest run`.

### 5. `cdk/test/cdk.test.ts`

No changes needed — tests use `aws-cdk-lib/assertions` and don't import from the alpha package.

## Error Handling

- **Compilation failure**: Would indicate an API mismatch — fix by adapting to any renamed properties (unlikely at same CDK version).
- **Synthesis failure**: Would indicate construct validation differences — check CDK release notes.
- **Test assertion failure**: Would indicate different CloudFormation output — update test assertions if needed.

## Correctness Properties

*Properties that should hold true after migration.*

### Property 1: Runtime resource configuration preservation

*For any* valid `AgentStackProps` (with optional bedrockModelID, notificationEmails, and schedules), synthesizing the stack SHALL produce an `AWS::BedrockAgentCore::Runtime` resource whose `AgentRuntimeName` derives from the stack name, whose `Description` matches the provided description, and whose `EnvironmentVariables` include all expected keys plus `BEDROCK_MODEL_ID` if and only if `bedrockModelID` is provided.

**Validates: Requirements 4.1**

### Property 2: SNS subscription count matches notification emails

*For any* list of notification email addresses provided in `notificationEmails`, the synthesized template SHALL contain exactly that many `AWS::SNS::Subscription` resources, and zero when the list is empty or omitted.

**Validates: Requirements 4.4**

### Property 3: EventBridge schedule count and configuration

*For any* list of `ScheduleConfig` objects provided in `schedules`, the synthesized template SHALL contain exactly that many `AWS::Scheduler::Schedule` resources, each with a `ScheduleExpression` matching the config's `schedule` value (defaulting to `rate(7 days)`) and a `Description` of `Job search: {company}`.

**Validates: Requirements 4.5**
