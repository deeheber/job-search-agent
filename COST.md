# What It Costs

Real numbers from running this project: about **$10–14/month**. The infrastructure is roughly 50¢/month; the LLM inference is everything else.

> **Disclaimer:** These figures come from actual AWS Cost Explorer data for **May–July 2026**, for a single deployment in us-west-2. AWS pricing, free tiers, and model rates change. Verify against [Amazon Bedrock pricing](https://aws.amazon.com/bedrock/pricing/) and [AgentCore pricing](https://aws.amazon.com/bedrock/agentcore/pricing/) before relying on these numbers.

## Usage Profile

The numbers below reflect this workload:

- 5 weekly EventBridge schedules (one company per weekday), about 22 agent runs/month
- `MODEL_PROVIDER=bedrock` with Claude Sonnet 4.6 (the model at the time; the current default is Sonnet 5)
- Each agent run costs roughly **$0.45–0.65**, nearly all of it model inference

## Monthly Breakdown

| Service | Cost/month | Notes |
|---|---|---|
| Bedrock model inference | **~$10–14** | ~95% of the total (May $12.65, Jun $9.94, Jul $13.57) |
| Bedrock AgentCore Runtime | **~$0.20–0.30** | Consumption-based (GB-hours + vCPU-hours); no idle charge |
| ECR (container images) | **~$0.07–0.25** | Grows as deployed runtime versions accumulate |
| CloudWatch (logs/metrics) | **~$0.01–0.02** | Mostly inside the 5 GB/month free ingest tier |
| EventBridge Scheduler | **$0** | 22 invocations vs. 14M free/month |
| SNS (email alerts) | **$0** | First 1,000 email notifications/month free |
| SQS (scheduler DLQ) | **$0** | First 1M requests/month free |
| SSM Parameter Store | **$0** | Standard-tier parameters are free |
| KMS | **$0** | AWS-managed key, within the free request tier |
| S3 (CDK assets) | **~pennies** | Bootstrap staging bucket |
| **Total** | **≈ $10–14/month** | |

## Scheduled Runs vs. Development

The totals above are actual charges, which include manual test invokes and deploy-day smoke tests alongside the scheduled runs. A steady-state "set it and forget it" month (schedules only) comes out to roughly **$9–11/month** (22 runs × ~$0.45–0.55). Testing barely moves the infrastructure rows; the difference is almost entirely model inference.

## Model Provider Matters

These numbers are from a `MODEL_PROVIDER=bedrock` deployment, so model inference shows up on the AWS bill. The repo's *default* is `MODEL_PROVIDER=anthropic`, which calls the Anthropic API directly. With that config, inference bills to your Anthropic account at [Anthropic API pricing](https://claude.com/pricing) instead, and the AWS bill only shows the ~50¢ of infrastructure. Cost also varies by model; see [Change the Model or Provider](DEPLOYMENT.md#change-the-model-or-provider).

## External: Tavily

Web search cost **$0**. At ~22 runs/month with a handful of search/extract calls per run, this usage fits well within Tavily's free tier (1,000 API credits/month at the time of writing). Heavier schedules would eventually need a paid plan; see [Tavily pricing](https://www.tavily.com/pricing) for current limits.
