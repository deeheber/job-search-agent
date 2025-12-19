import { Stack, StackProps, CfnOutput } from 'aws-cdk-lib'
import {
  Role,
  ServicePrincipal,
  PolicyDocument,
  PolicyStatement,
  Effect,
} from 'aws-cdk-lib/aws-iam'
import { Platform } from 'aws-cdk-lib/aws-ecr-assets'
import { Construct } from 'constructs'
import { Runtime, AgentRuntimeArtifact } from '@aws-cdk/aws-bedrock-agentcore-alpha'
import * as path from 'path'

interface StrandsAgentStackProps extends StackProps {
  bedrockModelID?: string | undefined
}

export class StrandsAgentStack extends Stack {
  constructor(scope: Construct, id: string, props: StrandsAgentStackProps) {
    super(scope, id, props)

    // IAM Role for AgentCore Runtime
    const agentRole = new Role(this, 'AgentCoreRole', {
      assumedBy: new ServicePrincipal('bedrock-agentcore.amazonaws.com'),
      inlinePolicies: {
        AgentCorePolicy: new PolicyDocument({
          statements: [
            // ECR access for container images
            new PolicyStatement({
              sid: 'ECRAccess',
              effect: Effect.ALLOW,
              actions: [
                'ecr:BatchGetImage',
                'ecr:GetDownloadUrlForLayer',
                'ecr:BatchCheckLayerAvailability',
                'ecr:GetAuthorizationToken',
              ],
              resources: [
                `arn:aws:ecr:${this.region}:${this.account}:repository/cdk-*`,
                '*', // GetAuthorizationToken requires wildcard
              ],
            }),
            // CloudWatch Logs for AgentCore
            new PolicyStatement({
              sid: 'CloudWatchLogs',
              effect: Effect.ALLOW,
              actions: ['logs:CreateLogGroup', 'logs:CreateLogStream', 'logs:PutLogEvents'],
              resources: [
                `arn:aws:logs:${this.region}:${this.account}:log-group:/aws/bedrock-agentcore/runtimes/*`,
              ],
            }),
            // Observability (X-Ray and CloudWatch metrics)
            new PolicyStatement({
              sid: 'Observability',
              effect: Effect.ALLOW,
              actions: [
                'xray:PutTraceSegments',
                'xray:PutTelemetryRecords',
                'cloudwatch:PutMetricData',
              ],
              resources: ['*'],
              conditions: {
                StringEquals: {
                  'cloudwatch:namespace': 'bedrock-agentcore',
                },
              },
            }),
            // Bedrock models and inference profiles
            // TODO: scope down to models used
            new PolicyStatement({
              sid: 'BedrockModels',
              effect: Effect.ALLOW,
              actions: ['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'],
              resources: [
                'arn:aws:bedrock:*::foundation-model/*',
                `arn:aws:bedrock:${this.region}:${this.account}:inference-profile/*`,
              ],
            }),
          ],
        }),
      },
    })

    // Build Docker image from local agent code
    const agentArtifact = AgentRuntimeArtifact.fromAsset(path.join(__dirname, '../../agent'), {
      platform: Platform.LINUX_ARM64,
      // https://github.com/aws/aws-cdk-cli/issues/650
      extraHash: `${this.account}-${this.region}`,
    })

    // Create AgentCore Runtime
    const runtime = new Runtime(this, 'StrandsAgentRuntime', {
      runtimeName: `${this.stackName.replace(/-/g, '_')}_StrandsAgent`,
      agentRuntimeArtifact: agentArtifact,
      executionRole: agentRole,
      description: 'Strands agent with calculator, time, and letter counter tools',
      environmentVariables: {
        AWS_REGION: this.region,
        AWS_DEFAULT_REGION: this.region,
        LOG_LEVEL: 'INFO',
        ...(props.bedrockModelID && { BEDROCK_MODEL_ID: props.bedrockModelID }),
      },
    })

    // Outputs
    new CfnOutput(this, 'RuntimeId', {
      description: 'AgentCore Runtime ID',
      value: runtime.agentRuntimeId,
    })

    new CfnOutput(this, 'RuntimeArn', {
      description: 'AgentCore Runtime ARN',
      value: runtime.agentRuntimeArn,
    })
  }
}
