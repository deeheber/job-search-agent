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

    it('configures ECR permissions for container image access', () => {
      template.hasResourceProperties('AWS::IAM::Role', {
        Policies: [
          {
            PolicyDocument: {
              Statement: Match.arrayWith([
                Match.objectLike({
                  Sid: 'ECRAccess',
                  Effect: 'Allow',
                  Action: [
                    'ecr:BatchGetImage',
                    'ecr:GetDownloadUrlForLayer',
                    'ecr:BatchCheckLayerAvailability',
                    'ecr:GetAuthorizationToken',
                  ],
                  Resource: [
                    Match.stringLikeRegexp('arn:aws:ecr:.+:.+:repository/cdk-\\*'),
                    '*', // GetAuthorizationToken requires wildcard
                  ],
                }),
              ]),
            },
          },
        ],
      })
    })

    it('configures CloudWatch logs permissions', () => {
      template.hasResourceProperties('AWS::IAM::Role', {
        Policies: [
          {
            PolicyDocument: {
              Statement: Match.arrayWith([
                Match.objectLike({
                  Sid: 'CloudWatchLogs',
                  Effect: 'Allow',
                  Action: ['logs:CreateLogGroup', 'logs:CreateLogStream', 'logs:PutLogEvents'],
                  Resource: Match.stringLikeRegexp(
                    'arn:aws:logs:.+:.+:log-group:/aws/bedrock-agentcore/runtimes/\\*'
                  ),
                }),
              ]),
            },
          },
        ],
      })
    })

    it('configures observability permissions for X-Ray and CloudWatch metrics', () => {
      template.hasResourceProperties('AWS::IAM::Role', {
        Policies: [
          {
            PolicyDocument: {
              Statement: Match.arrayWith([
                Match.objectLike({
                  Sid: 'Observability',
                  Effect: 'Allow',
                  Action: [
                    'xray:PutTraceSegments',
                    'xray:PutTelemetryRecords',
                    'cloudwatch:PutMetricData',
                  ],
                  Resource: '*',
                  Condition: {
                    StringEquals: {
                      'cloudwatch:namespace': 'bedrock-agentcore',
                    },
                  },
                }),
              ]),
            },
          },
        ],
      })
    })

    it('configures SNS publish permissions scoped to notification topic', () => {
      template.hasResourceProperties('AWS::IAM::Policy', {
        PolicyDocument: {
          Statement: Match.arrayWith([
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

    it('configures Bedrock model invocation permissions', () => {
      template.hasResourceProperties('AWS::IAM::Role', {
        Policies: [
          {
            PolicyDocument: {
              Statement: Match.arrayWith([
                Match.objectLike({
                  Sid: 'BedrockModels',
                  Effect: 'Allow',
                  Action: ['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'],
                  Resource: [
                    'arn:aws:bedrock:*::foundation-model/*',
                    Match.stringLikeRegexp('arn:aws:bedrock:.+:.+:inference-profile/\\*'),
                  ],
                }),
              ]),
            },
          },
        ],
      })
    })
  })

  describe('Required Resources', () => {
    it('creates exactly one IAM role, runtime, and SNS topic', () => {
      template.resourceCountIs('AWS::IAM::Role', 1)
      template.resourceCountIs('AWS::BedrockAgentCore::Runtime', 1)
      template.resourceCountIs('AWS::SNS::Topic', 1)
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

  describe('AgentRuntimeArtifact Configuration', () => {
    it('configures container artifact correctly', () => {
      template.hasResourceProperties('AWS::BedrockAgentCore::Runtime', {
        AgentRuntimeArtifact: {
          ContainerConfiguration: {
            ContainerUri: {
              'Fn::Sub': Match.stringLikeRegexp('.*\\.dkr\\.ecr\\..+\\..*/.*:.*'),
            },
          },
        },
      })
    })

    it('creates ECR access policy for container deployment', () => {
      // CDK creates IAM policy for ECR access and SNS publish
      template.resourceCountIs('AWS::IAM::Policy', 1)

      template.hasResourceProperties('AWS::IAM::Policy', {
        PolicyDocument: {
          Statement: Match.arrayWith([
            Match.objectLike({
              Action: Match.arrayWith([
                'ecr:BatchCheckLayerAvailability',
                'ecr:GetDownloadUrlForLayer',
                'ecr:BatchGetImage',
              ]),
              Effect: 'Allow',
            }),
          ]),
        },
      })
    })
  })

  describe('Security Validation', () => {
    it('ensures permissions follow principle of least privilege', () => {
      // Verify that ECR permissions are scoped to account resources where possible
      template.hasResourceProperties('AWS::IAM::Role', {
        Policies: [
          {
            PolicyDocument: {
              Statement: Match.arrayWith([
                Match.objectLike({
                  Sid: 'ECRAccess',
                  Resource: Match.arrayWith([
                    Match.stringLikeRegexp('arn:aws:ecr:.+:.+:repository/cdk-\\*'),
                  ]),
                }),
              ]),
            },
          },
        ],
      })

      // Verify CloudWatch logs are scoped to AgentCore log groups
      template.hasResourceProperties('AWS::IAM::Role', {
        Policies: [
          {
            PolicyDocument: {
              Statement: Match.arrayWith([
                Match.objectLike({
                  Sid: 'CloudWatchLogs',
                  Action: ['logs:CreateLogGroup', 'logs:CreateLogStream', 'logs:PutLogEvents'],
                  Resource: Match.stringLikeRegexp(
                    'arn:aws:logs:.+:.+:log-group:/aws/bedrock-agentcore/runtimes/\\*'
                  ),
                }),
              ]),
            },
          },
        ],
      })

      // Verify CloudWatch metrics are scoped to bedrock-agentcore namespace
      template.hasResourceProperties('AWS::IAM::Role', {
        Policies: [
          {
            PolicyDocument: {
              Statement: Match.arrayWith([
                Match.objectLike({
                  Sid: 'Observability',
                  Action: Match.arrayWith(['cloudwatch:PutMetricData']),
                  Condition: {
                    StringEquals: {
                      'cloudwatch:namespace': 'bedrock-agentcore',
                    },
                  },
                }),
              ]),
            },
          },
        ],
      })
    })
  })

  describe('SNS Notifications', () => {
    it('does not create email subscription when notificationEmail is not provided', () => {
      template.resourceCountIs('AWS::SNS::Subscription', 0)
    })

    it('creates email subscription when notificationEmail is provided', () => {
      const appWithEmail = new App()
      const stackWithEmail = new JobSearchAgentStack(appWithEmail, 'TestStackWithEmail', {
        notificationEmail: 'test@example.com',
        env: { account: '123456789012', region: 'us-west-2' },
      })
      const templateWithEmail = Template.fromStack(stackWithEmail)

      templateWithEmail.resourceCountIs('AWS::SNS::Subscription', 1)
      templateWithEmail.hasResourceProperties('AWS::SNS::Subscription', {
        Protocol: 'email',
        Endpoint: 'test@example.com',
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
