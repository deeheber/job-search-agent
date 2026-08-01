#!/usr/bin/env node
import { App } from 'aws-cdk-lib'
import { z } from 'zod'

import { JobSearchAgentStack, ScheduleConfig } from '../lib/job-search-agent-stack'

const scheduleSchema = z.object({
  company: z.string().min(1),
  title: z.string().optional(),
  location: z.string().optional(),
  schedule: z
    .string()
    .regex(/^(cron|rate)\(/, 'must be a cron(...) or rate(...) expression')
    .optional(),
})

const envSchema = z
  .object({
    CDK_DEFAULT_ACCOUNT: z.string().optional(),
    CDK_DEFAULT_REGION: z.string().optional(),
    AWS_DEFAULT_ACCOUNT_ID: z.string().optional(),
    AWS_DEFAULT_REGION: z.string().optional(),
    MODEL_PROVIDER: z
      .string()
      .transform((s) => (s === '' ? undefined : s))
      .pipe(z.enum(['bedrock', 'anthropic']).optional())
      .optional(),
    BEDROCK_MODEL_ID: z
      .string()
      .transform((s) => (s === '' ? undefined : s))
      .optional(),
    ANTHROPIC_MODEL_ID: z
      .string()
      .transform((s) => (s === '' ? undefined : s))
      .optional(),
    NOTIFICATION_EMAILS: z
      .string()
      .transform((s) => (s === '' ? undefined : s))
      .optional(),
    SCHEDULES: z
      .string()
      .transform((s) => (s === '' ? undefined : s))
      .optional()
      .transform((s, ctx) => {
        if (s === undefined) return undefined
        try {
          return JSON.parse(s) as unknown
        } catch {
          ctx.addIssue({ code: 'custom', message: 'must be valid JSON' })
          return z.NEVER
        }
      })
      .pipe(z.array(scheduleSchema).optional()),
    STACK_NAME: z
      .string()
      .transform((s) => (s === '' ? undefined : s))
      .optional()
      .default('JobSearchAgentStack'),
  })
  .refine((data) => data.CDK_DEFAULT_ACCOUNT ?? data.AWS_DEFAULT_ACCOUNT_ID, {
    message:
      '❌ AWS account not found. Please configure AWS CLI credentials by running "aws configure", set AWS_PROFILE environment variable, or set CDK_DEFAULT_ACCOUNT environment variable.',
  })
  .refine((data) => data.CDK_DEFAULT_REGION ?? data.AWS_DEFAULT_REGION, {
    message:
      '❌ AWS region not found. Please configure AWS CLI credentials by running "aws configure", set AWS_PROFILE environment variable, or set CDK_DEFAULT_REGION environment variable.',
  })

const parsed = envSchema.safeParse(process.env)
if (!parsed.success) {
  console.error(z.prettifyError(parsed.error))
  process.exit(1)
}
const env = parsed.data

const account = (env.CDK_DEFAULT_ACCOUNT ?? env.AWS_DEFAULT_ACCOUNT_ID)!
const region = (env.CDK_DEFAULT_REGION ?? env.AWS_DEFAULT_REGION)!
const modelProvider = env.MODEL_PROVIDER ?? undefined
const bedrockModelID = env.BEDROCK_MODEL_ID ?? undefined
const anthropicModelID = env.ANTHROPIC_MODEL_ID ?? undefined
const notificationEmails = env.NOTIFICATION_EMAILS?.split(',')
  .map((e) => e.trim())
  .filter(Boolean)
const schedules: ScheduleConfig[] | undefined = env.SCHEDULES

const app = new App()
new JobSearchAgentStack(app, env.STACK_NAME, {
  description: 'Job Search Agent infrastructure',
  modelProvider,
  bedrockModelID,
  anthropicModelID,
  notificationEmails,
  schedules,
  env: { account, region },
})
