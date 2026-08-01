import { describe, it, expect, beforeEach } from 'vitest'
import { App } from 'aws-cdk-lib'
import { Template, Match } from 'aws-cdk-lib/assertions'
import { JobSearchAgentStack } from '../lib/job-search-agent-stack'

const makeScheduleTemplate = () => {
  const app = new App()
  const stack = new JobSearchAgentStack(app, 'TestScheduleStack', {
    env: { account: '123456789012', region: 'us-west-2' },
    schedules: [
      { company: 'Google', title: 'Software Engineer', location: 'Remote' },
      { company: 'Meta', schedule: 'cron(0 12 ? * MON *)' },
    ],
  })
  return Template.fromStack(stack)
}

// Replace dynamic containerUri hash with stable placeholder for snapshot testing
const normalize = (template: Template): unknown =>
  JSON.parse(JSON.stringify(template.toJSON()).replace(/:[\da-f]{64}"/g, ':MOCKED_CONTAINER_HASH"'))

describe('JobSearchAgentStack', () => {
  let app: App
  let stack: JobSearchAgentStack
  let template: Template

  beforeEach(() => {
    app = new App()
    stack = new JobSearchAgentStack(app, 'TestJobSearchAgentStack', {
      env: {
        account: '123456789012',
        region: 'us-west-2',
      },
    })
    template = Template.fromStack(stack)
  })

  describe('IAM Role and Permissions', () => {
    it('creates AgentCore IAM role with correct trust relationship', () => {
      template.hasResourceProperties('AWS::IAM::Role', {
        AssumeRolePolicyDocument: {
          Statement: [
            {
              Effect: 'Allow',
              Principal: {
                Service: 'bedrock-agentcore.amazonaws.com',
              },
              Action: 'sts:AssumeRole',
            },
          ],
        },
      })
    })

    it('configures manually added permissions in DefaultPolicy', () => {
      template.hasResourceProperties('AWS::IAM::Policy', {
        PolicyDocument: {
          Statement: Match.arrayWith([
            Match.objectLike({
              Action: ['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'],
              Effect: 'Allow',
              Resource: [
                'arn:aws:bedrock:*::foundation-model/anthropic.*',
                Match.stringLikeRegexp('arn:aws:bedrock:.+:.+:inference-profile/\\*'),
              ],
            }),
            Match.objectLike({
              Action: 'ssm:GetParameter',
              Effect: 'Allow',
              Resource: [
                Match.stringLikeRegexp(
                  'arn:aws:ssm:.+:.+:parameter/job-search-agent/tavily-api-key'
                ),
                Match.stringLikeRegexp(
                  'arn:aws:ssm:.+:.+:parameter/job-search-agent/anthropic-api-key'
                ),
              ],
            }),
            Match.objectLike({
              Action: 'kms:Decrypt',
              Effect: 'Allow',
              Resource: '*',
              Condition: {
                StringEquals: {
                  'kms:ViaService': 'ssm.us-west-2.amazonaws.com',
                },
              },
            }),
            Match.objectLike({
              Action: 'sns:Publish',
              Effect: 'Allow',
              Resource: {
                Ref: Match.stringLikeRegexp('JobSearchNotificationTopic.*'),
              },
            }),
          ]),
        },
      })
    })
  })

  describe('Required Resources', () => {
    it('creates no schedules when schedules prop is not provided', () => {
      template.resourceCountIs('AWS::Scheduler::Schedule', 0)
    })

    it('creates AgentCore runtime with proper configuration', () => {
      template.hasResourceProperties('AWS::BedrockAgentCore::Runtime', {
        AgentRuntimeName: 'TestJobSearchAgentStack_JobSearchAgent',
        Description: 'Job search agent with web search, page extraction, and time',
        RoleArn: {
          'Fn::GetAtt': [Match.stringLikeRegexp('AgentCoreRole.*'), 'Arn'],
        },
      })
    })

    it('configures required environment variables', () => {
      template.hasResourceProperties('AWS::BedrockAgentCore::Runtime', {
        EnvironmentVariables: {
          AWS_REGION: 'us-west-2',
          AWS_DEFAULT_REGION: 'us-west-2',
          LOG_LEVEL: 'INFO',
          MODEL_PROVIDER: 'anthropic',
          TAVILY_API_KEY_SSM_PARAMETER: '/job-search-agent/tavily-api-key',
          ANTHROPIC_API_KEY_SSM_PARAMETER: '/job-search-agent/anthropic-api-key',
          SNS_TOPIC_ARN: {
            Ref: Match.stringLikeRegexp('JobSearchNotificationTopic.*'),
          },
        },
      })
    })

    it('does not set model ID env vars by default', () => {
      template.hasResourceProperties('AWS::BedrockAgentCore::Runtime', {
        EnvironmentVariables: Match.objectLike({
          BEDROCK_MODEL_ID: Match.absent(),
          ANTHROPIC_MODEL_ID: Match.absent(),
        }),
      })
    })

    it('passes model provider and model ID overrides to the runtime', () => {
      const providerApp = new App()
      const providerStack = new JobSearchAgentStack(providerApp, 'TestProviderStack', {
        modelProvider: 'bedrock',
        bedrockModelID: 'custom-bedrock-model',
        anthropicModelID: 'claude-opus-5',
        env: { account: '123456789012', region: 'us-west-2' },
      })
      const providerTemplate = Template.fromStack(providerStack)

      providerTemplate.hasResourceProperties('AWS::BedrockAgentCore::Runtime', {
        EnvironmentVariables: Match.objectLike({
          MODEL_PROVIDER: 'bedrock',
          BEDROCK_MODEL_ID: 'custom-bedrock-model',
          ANTHROPIC_MODEL_ID: 'claude-opus-5',
        }),
      })
    })
  })

  describe('SNS Notifications', () => {
    it('does not create email subscription when notificationEmails is not provided', () => {
      template.resourceCountIs('AWS::SNS::Subscription', 0)
    })

    it('creates email subscription for each notificationEmails entry', () => {
      const appWithEmail = new App()
      const stackWithEmail = new JobSearchAgentStack(appWithEmail, 'TestStackWithEmail', {
        notificationEmails: ['a@example.com', 'b@example.com'],
        env: { account: '123456789012', region: 'us-west-2' },
      })
      const templateWithEmail = Template.fromStack(stackWithEmail)

      templateWithEmail.resourceCountIs('AWS::SNS::Subscription', 2)
    })
  })

  describe('EventBridge Schedules', () => {
    let scheduleTemplate: Template

    beforeEach(() => {
      scheduleTemplate = makeScheduleTemplate()
    })

    it('creates one schedule per configured company', () => {
      scheduleTemplate.resourceCountIs('AWS::Scheduler::Schedule', 2)
    })

    it('uses default rate(7 days) when no schedule expression provided', () => {
      scheduleTemplate.hasResourceProperties('AWS::Scheduler::Schedule', {
        ScheduleExpression: 'rate(7 days)',
        Description: 'Job search: Google',
      })
    })

    it('uses custom expression when schedule is provided', () => {
      scheduleTemplate.hasResourceProperties('AWS::Scheduler::Schedule', {
        ScheduleExpression: 'cron(0 12 ? * MON *)',
        Description: 'Job search: Meta',
      })
    })

    it('passes company, title, and location in schedule payload', () => {
      scheduleTemplate.hasResourceProperties('AWS::Scheduler::Schedule', {
        Description: 'Job search: Google',
        Target: Match.objectLike({
          Input: {
            'Fn::Join': [
              '',
              Match.arrayWith([
                Match.stringLikeRegexp(
                  '.*company.*Google.*title.*Software Engineer.*location.*Remote.*'
                ),
              ]),
            ],
          },
        }),
      })
    })

    it('names schedules after the company so reordering does not retarget them', () => {
      scheduleTemplate.hasResourceProperties('AWS::Scheduler::Schedule', {
        Name: 'TestScheduleStack-Schedule-Google',
      })
      scheduleTemplate.hasResourceProperties('AWS::Scheduler::Schedule', {
        Name: 'TestScheduleStack-Schedule-Meta',
      })
    })

    it('configures retries, DLQ, and a flexible time window on each schedule', () => {
      scheduleTemplate.hasResourceProperties('AWS::Scheduler::Schedule', {
        FlexibleTimeWindow: { Mode: 'FLEXIBLE', MaximumWindowInMinutes: 120 },
        Target: Match.objectLike({
          RetryPolicy: Match.objectLike({ MaximumRetryAttempts: 2 }),
          DeadLetterConfig: {
            Arn: { 'Fn::GetAtt': [Match.stringLikeRegexp('Schedulerdlq.*'), 'Arn'] },
          },
        }),
      })
    })

    it('scopes the scheduler role to the runtime ARN', () => {
      scheduleTemplate.hasResourceProperties('AWS::IAM::Policy', {
        PolicyDocument: {
          Statement: Match.arrayWith([
            Match.objectLike({
              Action: 'bedrock-agentcore:InvokeAgentRuntime',
              Resource: [
                {
                  'Fn::GetAtt': [
                    Match.stringLikeRegexp('JobSearchAgentRuntime.*'),
                    'AgentRuntimeArn',
                  ],
                },
                {
                  'Fn::Join': [
                    '',
                    [
                      {
                        'Fn::GetAtt': [
                          Match.stringLikeRegexp('JobSearchAgentRuntime.*'),
                          'AgentRuntimeArn',
                        ],
                      },
                      '/*',
                    ],
                  ],
                },
              ],
            }),
          ]),
        },
      })
    })

    it('alarms on DLQ messages to the notification topic', () => {
      scheduleTemplate.hasResourceProperties('AWS::CloudWatch::Alarm', {
        MetricName: 'ApproximateNumberOfMessagesVisible',
        Threshold: 1,
        AlarmActions: [{ Ref: Match.stringLikeRegexp('JobSearchNotificationTopic.*') }],
      })
    })
  })

  describe('CloudFormation Template Snapshot', () => {
    it('matches the expected template structure', () => {
      expect(normalize(template)).toMatchSnapshot()
    })

    it('matches the expected template structure with schedules', () => {
      expect(normalize(makeScheduleTemplate())).toMatchSnapshot()
    })
  })
})
