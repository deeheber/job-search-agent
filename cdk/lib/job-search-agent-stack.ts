import { Stack, StackProps, CfnOutput, Duration } from 'aws-cdk-lib'
import { Alarm, TreatMissingData } from 'aws-cdk-lib/aws-cloudwatch'
import { SnsAction } from 'aws-cdk-lib/aws-cloudwatch-actions'
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

// SSM parameter names, created out-of-band (never by this stack); read by the agent at
// invocation time (the Anthropic one only when MODEL_PROVIDER=anthropic)
const TAVILY_API_KEY_SSM_PARAMETER = '/job-search-agent/tavily-api-key'
const ANTHROPIC_API_KEY_SSM_PARAMETER = '/job-search-agent/anthropic-api-key'

export interface ScheduleConfig {
  company: string
  title?: string | undefined
  location?: string | undefined
  schedule?: string | undefined // EventBridge expression, e.g. "cron(0 12 ? * MON *)" or "rate(14 days)"
}

interface AgentStackProps extends StackProps {
  modelProvider?: 'bedrock' | 'anthropic' | undefined
  bedrockModelID?: string | undefined
  anthropicModelID?: string | undefined
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
          // region wildcard: cross-region inference profiles invoke the model outside this.region
          'arn:aws:bedrock:*::foundation-model/anthropic.*',
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
          `arn:aws:ssm:${this.region}:${this.account}:parameter${ANTHROPIC_API_KEY_SSM_PARAMETER}`,
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
      description: 'Job search agent with web search, page extraction, and time',
      environmentVariables: {
        AWS_REGION: this.region,
        AWS_DEFAULT_REGION: this.region,
        LOG_LEVEL: 'INFO',
        MODEL_PROVIDER: props.modelProvider ?? 'anthropic',
        TAVILY_API_KEY_SSM_PARAMETER: TAVILY_API_KEY_SSM_PARAMETER,
        ANTHROPIC_API_KEY_SSM_PARAMETER: ANTHROPIC_API_KEY_SSM_PARAMETER,
        SNS_TOPIC_ARN: notificationTopic.topicArn,
        ...(props.bedrockModelID && { BEDROCK_MODEL_ID: props.bedrockModelID }),
        ...(props.anthropicModelID && { ANTHROPIC_MODEL_ID: props.anthropicModelID }),
      },
    })

    if (props.schedules && props.schedules.length > 0) {
      const dlq = new Queue(this, 'Scheduler-dlq', {
        queueName: `${this.stackName}-scheduler-dlq`,
        retentionPeriod: Duration.days(14),
      })

      new Alarm(this, 'SchedulerDlqAlarm', {
        alarmName: `${this.stackName}-scheduler-dlq-alarm`,
        alarmDescription: 'Scheduled job search invocations are failing and landing in the DLQ',
        metric: dlq.metricApproximateNumberOfMessagesVisible(),
        threshold: 1,
        evaluationPeriods: 1,
        treatMissingData: TreatMissingData.NOT_BREACHING,
      }).addAlarmAction(new SnsAction(notificationTopic))

      // Company-keyed IDs so reordering SCHEDULES doesn't retarget deployed schedules
      const scheduleIdCounts = new Map<string, number>()
      for (const config of props.schedules) {
        const payload: Record<string, string> = { company: config.company }
        if (config.title) payload.title = config.title
        if (config.location) payload.location = config.location

        const scheduleExpr = config.schedule
          ? ScheduleExpression.expression(config.schedule)
          : ScheduleExpression.rate(Duration.days(7))

        const base = config.company.replace(/[^A-Za-z0-9_-]/g, '-').slice(0, 30)
        const count = scheduleIdCounts.get(base) ?? 0
        scheduleIdCounts.set(base, count + 1)
        const scheduleId = count === 0 ? base : `${base}-${count + 1}`

        new Schedule(this, `Schedule-${scheduleId}`, {
          schedule: scheduleExpr,
          scheduleName: `${this.stackName}-Schedule-${scheduleId}`,
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
                resources: [runtime.agentRuntimeArn, `${runtime.agentRuntimeArn}/*`],
              }),
            ],
            retryAttempts: 2,
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

    new CfnOutput(this, 'AnthropicApiKeyParameter', {
      description:
        'SSM Parameter name for Anthropic API Key (must be created before deployment when MODEL_PROVIDER is anthropic)',
      value: ANTHROPIC_API_KEY_SSM_PARAMETER,
    })

    new CfnOutput(this, 'NotificationTopicArn', {
      description: 'SNS Topic ARN for job search notifications',
      value: notificationTopic.topicArn,
    })
  }
}
