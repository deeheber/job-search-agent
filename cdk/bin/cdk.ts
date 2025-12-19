#!/usr/bin/env node
import * as dotenv from 'dotenv'
import path from 'path'
import { App } from 'aws-cdk-lib'
import { StrandsAgentStack } from '../lib/strands-agent-stack'

dotenv.config({ path: path.join(__dirname, '../.env') })

const {
  AWS_DEFAULT_ACCOUNT_ID,
  AWS_DEFAULT_REGION,
  CDK_DEFAULT_ACCOUNT,
  CDK_DEFAULT_REGION,
  BEDROCK_MODEL_ID,
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

const app = new App()
new StrandsAgentStack(app, 'StrandsAgentStack', {
  description: 'Demo template for strands-agents',
  bedrockModelID,
  env: { account, region },
})
