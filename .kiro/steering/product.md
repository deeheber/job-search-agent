# Product Overview

Strands Agent Template - a CDK-based deployment template for Strands AI agents to AWS Bedrock AgentCore Runtime.

## Purpose

This is a template repository for deploying Strands-based AI agents to AWS Bedrock AgentCore Runtime using AWS CDK. It provides infrastructure-as-code for building Python agents that can use tools, process natural language requests, and execute tasks autonomously in a serverless environment.

**Target Audience**: Developers familiar with Python, AWS CDK, and AI agent development who want to deploy production-ready agents to AWS.

## Current State

- Python agent implementation using Strands framework with custom and community tools
- CDK infrastructure specifically designed for AWS Bedrock AgentCore Runtime deployment
- Single agent implementation (`agentcore_app.py`) that runs locally and deploys to AgentCore
- Uses `@aws-cdk/aws-bedrock-agentcore-alpha` constructs for AgentCore integration
- Currently implements multiple tools including calculator, current_time, http_request (community), and letter_counter (custom)
- Full CI/CD pipeline with GitHub Actions for both Python and TypeScript components
- Enhanced observability with OpenTelemetry integration for distributed tracing

## Deployment

The agent can be deployed to AWS Bedrock AgentCore Runtime, which provides:

- Serverless container hosting
- Automatic scaling
- Built-in observability (CloudWatch Logs, OpenTelemetry tracing)
- Integration with Bedrock foundation models

**Region**: The deployment region is automatically determined from your AWS CLI configuration. Ensure Bedrock AgentCore is available in your chosen region.

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
