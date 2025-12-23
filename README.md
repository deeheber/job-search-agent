# Job Search Agent

**🔍 AI-Powered Job Search Agent** - Automatically monitors company hiring status and provides detailed job opportunity insights.

This agent takes a company name as input and determines if the company is currently hiring. When opportunities are found, it responds with position titles, job descriptions, and application links. Built on AWS Bedrock AgentCore Runtime with enterprise-grade observability and CI/CD.

## What You Get

✅ **Job search intelligence** - Company hiring status with position details  
✅ **Multi-source integration** - Career pages and job board APIs  
✅ **Production-ready infrastructure** - CDK stack with IAM, logging, tracing  
✅ **Local development environment** - Test job searches before deploying  
✅ **Automated CI/CD** - GitHub Actions for Python + TypeScript  
✅ **Built-in observability** - CloudWatch logs, OpenTelemetry tracing

## Current Features

- **Single Company Search**: Input company name, get hiring status and job details
- **Real-time Results**: Fresh data from live job postings and career pages
- **Intelligent Parsing**: AI-powered extraction of position titles and application links
- **Timestamp Tracking**: Job posting dates and search freshness

## Future Roadmap

- **Multi-company Processing**: Batch search across multiple companies
- **Automated Scheduling**: EventBridge integration for periodic monitoring
- **Email Notifications**: SNS alerts when hiring opportunities are detected

## Why Python + TypeScript?

We chose Python for the agent implementation and TypeScript for infrastructure because each language offers the richest ecosystem for its respective framework. [Strands](https://strandsagents.com) provides first-class Python support with comprehensive documentation and tooling, while [AWS CDK](https://aws.amazon.com/cdk/) delivers the best developer experience through TypeScript. This gives you access to the most mature libraries, examples, and community resources for both domains.

As these frameworks evolve, we may consolidate to a single language for simplicity.

## Quick Start

```bash
# Test job search locally
cd agent && source .venv/bin/activate && python src/agentcore_app.py

# Test with input: {"company": "Panic Inc.", "title": "Software Engineer"}

# Deploy to AWS
aws configure && cd cdk && npm install && npm run build && cdk deploy
```

**Ready to search?** Deploy the agent to AWS and start monitoring company hiring status in under 10 minutes. ⚡️

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete setup instructions.
