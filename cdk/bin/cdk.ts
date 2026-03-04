#!/usr/bin/env node
import { App } from 'aws-cdk-lib'
import { z } from 'zod'

import { JobSearchAgentStack, ScheduleConfig } from '../lib/job-search-agent-stack'

const envSchema = z
  .object({
    CDK_DEFAULT_ACCOUNT: z.string().optional(),
    CDK_DEFAULT_REGION: z.string().optional(),
    AWS_DEFAULT_ACCOUNT_ID: z.string().optional(),
    AWS_DEFAULT_REGION: z.string().optional(),
    BEDROCK_MODEL_ID: z.string().optional(),
    NOTIFICATION_EMAILS: z.string().optional(),
    SCHEDULES: z.string().optional(),
    STACK_NAME: z.string().default('JobSearchAgentStack'),
  })
  .refine((data) => data.CDK_DEFAULT_ACCOUNT ?? data.AWS_DEFAULT_ACCOUNT_ID, {
    message:
      '❌ AWS account not found. Please configure AWS CLI credentials by running "aws configure", set AWS_PROFILE environment variable, or set CDK_DEFAULT_ACCOUNT environment variable.',
  })
  .refine((data) => data.CDK_DEFAULT_REGION ?? data.AWS_DEFAULT_REGION, {
    message:
      '❌ AWS region not found. Please configure AWS CLI credentials by running "aws configure", set AWS_PROFILE environment variable, or set CDK_DEFAULT_REGION environment variable.',
  })

const env = envSchema.parse(process.env)

const account = (env.CDK_DEFAULT_ACCOUNT ?? env.AWS_DEFAULT_ACCOUNT_ID)!
const region = (env.CDK_DEFAULT_REGION ?? env.AWS_DEFAULT_REGION)!
const bedrockModelID = env.BEDROCK_MODEL_ID ?? undefined
const notificationEmails = env.NOTIFICATION_EMAILS?.split(',')
  .map((e) => e.trim())
  .filter(Boolean)
const schedules: ScheduleConfig[] | undefined = env.SCHEDULES
  ? (JSON.parse(env.SCHEDULES) as ScheduleConfig[])
  : undefined

const app = new App()
new JobSearchAgentStack(app, env.STACK_NAME, {
  description: 'Job Search Agent infrastructure',
  bedrockModelID,
  notificationEmails,
  schedules,
  env: { account, region },
})
