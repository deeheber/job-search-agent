import { describe, it, expect, beforeEach } from 'vitest'
import { App } from 'aws-cdk-lib'
import { Template, Match } from 'aws-cdk-lib/assertions'
import { JobSearchAgentStack } from '../lib/job-search-agent-stack'

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
                'arn:aws:bedrock:*::foundation-model/*',
                Match.stringLikeRegexp('arn:aws:bedrock:.+:.+:inference-profile/\\*'),
              ],
            }),
            Match.objectLike({
              Action: 'ssm:GetParameter',
              Effect: 'Allow',
              Resource: Match.stringLikeRegexp(
                'arn:aws:ssm:.+:.+:parameter/job-search-agent/tavily-api-key'
              ),
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
        Description: 'Job search agent with web search, time, and http_request',
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
          SNS_TOPIC_ARN: {
            Ref: Match.stringLikeRegexp('JobSearchNotificationTopic.*'),
          },
        },
      })
    })

    it('creates stack outputs for runtime access', () => {
      template.hasOutput('RuntimeId', {
        Description: 'AgentCore Runtime ID',
        Value: {
          'Fn::GetAtt': [Match.stringLikeRegexp('JobSearchAgentRuntime.*'), 'AgentRuntimeId'],
        },
      })

      template.hasOutput('RuntimeArn', {
        Description: 'AgentCore Runtime ARN',
        Value: {
          'Fn::GetAtt': [Match.stringLikeRegexp('JobSearchAgentRuntime.*'), 'AgentRuntimeArn'],
        },
      })

      template.hasOutput('NotificationTopicArn', {
        Description: Match.stringLikeRegexp('SNS Topic ARN.*'),
        Value: {
          Ref: Match.stringLikeRegexp('JobSearchNotificationTopic.*'),
        },
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
      const scheduleApp = new App()
      const scheduleStack = new JobSearchAgentStack(scheduleApp, 'TestScheduleStack', {
        env: { account: '123456789012', region: 'us-west-2' },
        schedules: [
          { company: 'Google', title: 'Software Engineer', location: 'Remote' },
          { company: 'Meta', schedule: 'cron(0 12 ? * MON *)' },
        ],
      })
      scheduleTemplate = Template.fromStack(scheduleStack)
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
  })

  describe('CloudFormation Template Snapshot', () => {
    it('matches the expected template structure', () => {
      const templateJson = template.toJSON()

      // Replace dynamic containerUri hash with stable placeholder for snapshot testing
      const templateString = JSON.stringify(templateJson)
      const normalizedTemplate = templateString.replace(/:[\da-f]{64}"/g, ':MOCKED_CONTAINER_HASH"')

      expect(JSON.parse(normalizedTemplate)).toMatchSnapshot()
    })
  })
})
