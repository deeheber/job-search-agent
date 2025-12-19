# Strands Agent Template

**🚀 GitHub Template Repository** - Click "Use this template" to create your own production-ready AI agent in minutes, not days.

Skip the infrastructure setup and focus on what matters: building your agent. This template provides everything you need to deploy Strands AI agents to AWS Bedrock AgentCore Runtime with enterprise-grade observability, security, and CI/CD built-in.

## What You Get

✅ **Production-ready infrastructure** - CDK stack with IAM, logging, tracing  
✅ **Local development environment** - Test agents before deploying  
✅ **Automated CI/CD** - GitHub Actions for Python + TypeScript  
✅ **Built-in observability** - CloudWatch logs, OpenTelemetry tracing  
✅ **Quality tooling** - Automated testing, linting, formatting

## Why Python + TypeScript?

We chose Python for the agent implementation and TypeScript for infrastructure because each language offers the richest ecosystem for its respective framework. [Strands](https://strandsagents.com) provides first-class Python support with comprehensive documentation and tooling, while [AWS CDK](https://aws.amazon.com/cdk/) delivers the best developer experience through TypeScript. This gives you access to the most mature libraries, examples, and community resources for both domains.

As these frameworks evolve, we may consolidate to a single language for simplicity.

## Quick Start

```bash
# Test locally
cd agent && source .venv/bin/activate && python src/agentcore_app.py

# Deploy to AWS
aws configure && cd cdk && npm install && npm run build && cdk deploy
```

**Ready to build?** Replace the example agent code with your own and deploy to AWS in under 10 minutes. ⚡️

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete setup instructions.
