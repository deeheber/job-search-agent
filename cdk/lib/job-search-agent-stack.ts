import { Stack, StackProps, CfnOutput, Duration } from 'aws-cdk-lib'
import { Role, ServicePrincipal, PolicyStatement } from 'aws-cdk-lib/aws-iam'
import { Platform } from 'aws-cdk-lib/aws-ecr-assets'
import { Topic } from 'aws-cdk-lib/aws-sns'
import { EmailSubscription } from 'aws-cdk-lib/aws-sns-subscriptions'
import {
  Schedule,
  ScheduleExpression,
  ScheduleTargetInput,
  TimeWindow,
} from 'aws-cdk-lib/aws-scheduler'
import { Universal } from 'aws-cdk-lib/aws-scheduler-targets'
import { Construct } from 'constructs'
import { Runtime, AgentRuntimeArtifact } from 'aws-cdk-lib/aws-bedrockagentcore'
import * as path from 'path'
import { Queue } from 'aws-cdk-lib/aws-sqs'

// SSM parameter name for Tavily API key (must be created manually before deployment)
const TAVILY_API_KEY_SSM_PARAMETER = '/job-search-agent/tavily-api-key'

export interface ScheduleConfig {
  company: string
  title?: string
  location?: string
  schedule?: string // EventBridge expression, e.g. "cron(0 12 ? * MON *)" or "rate(14 days)"
}

interface AgentStackProps extends StackProps {
  bedrockModelID?: string | undefined
  notificationEmails?: string[] | undefined
  schedules?: ScheduleConfig[] | undefined
}

export class JobSearchAgentStack extends Stack {
  constructor(scope: Construct, id: string, props: AgentStackProps) {
    super(scope, id, props)

    const agentRole = new Role(this, 'AgentCoreRole', {
      roleName: `${this.stackName}-AgentCoreRole`,
      assumedBy: new ServicePrincipal('bedrock-agentcore.amazonaws.com'),
    })

    agentRole.addToPolicy(
      new PolicyStatement({
        sid: 'BedrockModels',
        actions: ['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'],
        resources: [
          'arn:aws:bedrock:*::foundation-model/*',
          `arn:aws:bedrock:${this.region}:${this.account}:inference-profile/*`,
        ],
      })
    )

    agentRole.addToPolicy(
      new PolicyStatement({
        sid: 'SSMParameterAccess',
        actions: ['ssm:GetParameter'],
        resources: [
          `arn:aws:ssm:${this.region}:${this.account}:parameter${TAVILY_API_KEY_SSM_PARAMETER}`,
        ],
      })
    )

    // KMS Decrypt for SSM parameter encryption
    agentRole.addToPolicy(
      new PolicyStatement({
        sid: 'KMSDecrypt',
        actions: ['kms:Decrypt'],
        resources: ['*'],
        conditions: {
          StringEquals: {
            'kms:ViaService': `ssm.${this.region}.amazonaws.com`,
          },
        },
      })
    )

    const notificationTopic = new Topic(this, 'JobSearchNotificationTopic', {
      topicName: `${this.stackName}-notify`,
      displayName: 'Job Search Agent Notifications',
    })

    for (const email of props.notificationEmails ?? []) {
      notificationTopic.addSubscription(new EmailSubscription(email))
    }

    notificationTopic.grantPublish(agentRole)

    const agentArtifact = AgentRuntimeArtifact.fromAsset(path.join(__dirname, '../../agent'), {
      platform: Platform.LINUX_ARM64,
      // https://github.com/aws/aws-cdk-cli/issues/650
      extraHash: `${this.account}-${this.region}`,
    })

    const runtime = new Runtime(this, 'JobSearchAgentRuntime', {
      runtimeName: `${this.stackName.replace(/-/g, '_')}_JobSearchAgent`,
      agentRuntimeArtifact: agentArtifact,
      executionRole: agentRole,
      description: 'Job search agent with web search, time, and http_request',
      environmentVariables: {
        AWS_REGION: this.region,
        AWS_DEFAULT_REGION: this.region,
        LOG_LEVEL: 'INFO',
        TAVILY_API_KEY_SSM_PARAMETER: TAVILY_API_KEY_SSM_PARAMETER,
        SNS_TOPIC_ARN: notificationTopic.topicArn,
        ...(props.bedrockModelID && { BEDROCK_MODEL_ID: props.bedrockModelID }),
      },
    })

    if (props.schedules && props.schedules.length > 0) {
      const dlq = new Queue(this, 'Scheduler-dlq', {
        queueName: `${this.stackName}-scheduler-dlq`,
        retentionPeriod: Duration.days(14),
      })

      for (const [index, config] of props.schedules.entries()) {
        const payload: Record<string, string> = { company: config.company }
        if (config.title) payload.title = config.title
        if (config.location) payload.location = config.location

        const scheduleExpr = config.schedule
          ? ScheduleExpression.expression(config.schedule)
          : ScheduleExpression.rate(Duration.days(7))

        new Schedule(this, `Schedule-${index}`, {
          schedule: scheduleExpr,
          scheduleName: `${this.stackName}-Schedule-${index}`,
          target: new Universal({
            service: 'bedrockagentcore',
            action: 'invokeAgentRuntime',
            input: ScheduleTargetInput.fromObject({
              AgentRuntimeArn: runtime.agentRuntimeArn,
              Payload: JSON.stringify(payload),
            }),
            policyStatements: [
              new PolicyStatement({
                actions: ['bedrock-agentcore:InvokeAgentRuntime'],
                resources: [`${runtime.agentRuntimeArn}*`],
              }),
            ],
            retryAttempts: 0,
            deadLetterQueue: dlq,
          }),
          timeWindow: TimeWindow.flexible(Duration.hours(2)),
          description: `Job search: ${config.company}`,
        })
      }
    }

    new CfnOutput(this, 'RuntimeId', {
      description: 'AgentCore Runtime ID',
      value: runtime.agentRuntimeId,
    })

    new CfnOutput(this, 'RuntimeArn', {
      description: 'AgentCore Runtime ARN',
      value: runtime.agentRuntimeArn,
    })

    new CfnOutput(this, 'TavilyApiKeyParameter', {
      description: 'SSM Parameter name for Tavily API Key (must be created before deployment)',
      value: TAVILY_API_KEY_SSM_PARAMETER,
    })

    new CfnOutput(this, 'NotificationTopicArn', {
      description: 'SNS Topic ARN for job search notifications',
      value: notificationTopic.topicArn,
    })
  }
}
