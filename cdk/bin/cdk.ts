#!/usr/bin/env node
import * as dotenv from 'dotenv'
import path from 'path'
import { App } from 'aws-cdk-lib'
import { JobSearchAgentStack } from '../lib/job-search-agent-stack'

dotenv.config({ path: path.join(__dirname, '../../agent/.env') })

const {
  AWS_DEFAULT_ACCOUNT_ID,
  AWS_DEFAULT_REGION,
  CDK_DEFAULT_ACCOUNT,
  CDK_DEFAULT_REGION,
  BEDROCK_MODEL_ID,
  TAVILY_API_KEY,
} = process.env

const account = CDK_DEFAULT_ACCOUNT ?? AWS_DEFAULT_ACCOUNT_ID
const region = CDK_DEFAULT_REGION ?? AWS_DEFAULT_REGION
const bedrockModelID = BEDROCK_MODEL_ID ?? undefined

if (!account || !region) {
  throw new Error(
    `❌ AWS account and region not found.

🔧 Please configure AWS CLI credentials by running "aws configure", set AWS_PROFILE environment variable, or set CDK_DEFAULT_ACCOUNT/CDK_DEFAULT_REGION environment variables.`
  )
}

if (!TAVILY_API_KEY) {
  throw new Error(
    `❌ TAVILY_API_KEY not found.

🔧 Add TAVILY_API_KEY to agent/.env. Get a free key at https://app.tavily.com`
  )
}

const app = new App()
new JobSearchAgentStack(app, 'JobSearchAgentStack', {
  description: 'Demo template for strands-agents',
  bedrockModelID,
  tavilyApiKey: TAVILY_API_KEY,
  env: { account, region },
})
