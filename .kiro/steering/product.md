# Job Search Agent

AI-powered agent that monitors company hiring status and provides job opportunity insights.

## Purpose

Takes company name as input → returns hiring status, position titles, and job description links.

**Target**: Job seekers, recruiters, career professionals

## Current Features

- Single company job search using Tavily web search API
- Real-time results from live job postings and career pages
- Optional email notifications via SNS when companies are hiring
- Strands framework with AgentCore Runtime deployment
- OpenTelemetry observability and CloudWatch Logs
- Secure API key management via SSM Parameter Store

## Roadmap

1. **Phase 1** (Current): Single company lookup + optional SNS notifications
2. **Phase 2**: EventBridge scheduling for periodic checks
