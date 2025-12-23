# Product Overview

Job Search Agent - an AI-powered agent that monitors company hiring status and provides job opportunity insights.

## Purpose

This agent takes a company name as input and determines if the company is currently hiring. When hiring opportunities are found, it responds with detailed information including position titles and links to job descriptions when available.

**Target Audience**: Job seekers, recruiters, and career professionals who want automated monitoring of hiring opportunities at specific companies.

## Current State

- Python agent implementation using Strands framework with job search capabilities
- CDK infrastructure specifically designed for AWS Bedrock AgentCore Runtime deployment
- Single company lookup functionality (`agentcore_app.py`) that runs locally and deploys to AgentCore
- Uses `@aws-cdk/aws-bedrock-agentcore-alpha` constructs for AgentCore integration
- Implements web scraping and job board API integration tools for comprehensive job search
- Full CI/CD pipeline with GitHub Actions for both Python and TypeScript components
- Enhanced observability with OpenTelemetry integration for distributed tracing

## Future Roadmap

**Phase 1 (Current)**: Single company job search

- Input: Company name
- Output: Hiring status, position titles, job description links

**Phase 2 (Planned)**: Multi-company batch processing

- Input: Multiple company names
- Output: Consolidated hiring report across all companies

**Phase 3 (Planned)**: Automated scheduling and notifications

- EventBridge Scheduler integration for periodic job monitoring
- SNS email notifications when hiring opportunities are detected
- Customizable monitoring frequency and alert preferences

## Key Features

- **Company Analysis**: Intelligent parsing of company career pages and job boards
- **Job Details**: Position titles, descriptions, application links, and posting dates
- **Multi-source Search**: Integration with major job platforms and company career sites
- **Real-time Results**: Fresh data from live job postings and career pages

## Prerequisites

- AWS Account with appropriate permissions
- Docker installed and running
- AWS CLI configured
- Node.js 24+ and Python 3.13+
- Bedrock model access enabled

## Getting Started

1. **Local Development**: Test the agent locally before deployment
2. **Infrastructure Setup**: Use CDK to deploy to AWS Bedrock AgentCore Runtime
3. **Monitoring**: Leverage built-in CloudWatch Logs and OpenTelemetry tracing

See the [DEPLOYMENT.md guide](../DEPLOYMENT.md) for complete step-by-step deployment instructions.
