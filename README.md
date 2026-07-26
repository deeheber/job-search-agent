> **Note:** This project was started before my current employment as a learning exercise. I'm completing it to finish what I started, not as an indication of active job searching.

# Job Search Agent

[![Awesome Strands Agents](https://img.shields.io/badge/Awesome-Strands%20Agents-00FF77?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjkwIiBoZWlnaHQ9IjQ2MyIgdmlld0JveD0iMCAwIDI5MCA0NjMiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik05Ny4yOTAyIDUyLjc4ODRDODUuMDY3NCA0OS4xNjY3IDcyLjIyMzQgNTYuMTM4OSA2OC42MDE3IDY4LjM2MTZDNjQuOTgwMSA4MC41ODQzIDcxLjk1MjQgOTMuNDI4MyA4NC4xNzQ5IDk3LjA1MDFMMjM1LjExNyAxMzkuNzc1QzI0NS4yMjMgMTQyLjc2OSAyNDYuMzU3IDE1Ni42MjggMjM2Ljg3NCAxNjEuMjI2TDMyLjU0NiAyNjAuMjkxQy0xNC45NDM5IDI4My4zMTYgLTkuMTYxMDcgMzUyLjc0IDQxLjQ4MzUgMzY3LjU5MUwxODkuNTUxIDQxMS4wMDlMMTkwLjEyNSA0MTEuMTY5QzIwMi4xODMgNDE0LjM3NiAyMTQuNjY1IDQwNy4zOTYgMjE4LjE5NiAzOTUuMzU1QzIyMS43ODQgMzgzLjEyMiAyMTQuNzc0IDM3MC4yOTYgMjAyLjU0MSAzNjYuNzA5TDU0LjQ3MzggMzIzLjI5MUM0NC4zNDQ3IDMyMC4zMjEgNDMuMTg3OSAzMDYuNDM2IDUyLjY4NTcgMzAxLjgzMUwyNTcuMDE0IDIwMi43NjZDMzA0LjQzMiAxNzkuNzc2IDI5OC43NTggMTEwLjQ4MyAyNDguMjMzIDk1LjUxMkw5Ny4yOTAyIDUyLjc4ODRaIiBmaWxsPSIjRkZGRkZGIi8+CjxwYXRoIGQ9Ik0yNTkuMTQ3IDAuOTgxODEyQzI3MS4zODkgLTIuNTc0OTggMjg0LjE5NyA0LjQ2NTcxIDI4Ny43NTQgMTYuNzA3NEMyOTEuMzExIDI4Ljk0OTIgMjg0LjI3IDQxLjc1NyAyNzIuMDI4IDQ1LjMxMzhMNzEuMTcyNyAxMDMuNjcxQzQwLjcxNDIgMTEyLjUyMSAzNy4xOTc2IDE1NC4yNjIgNjUuNzQ1OSAxNjguMDgzTDI0MS4zNDMgMjUzLjA5M0MzMDcuODcyIDI4NS4zMDIgMjk5Ljc5NCAzODIuNTQ2IDIyOC44NjIgNDAzLjMzNkwzMC40MDQxIDQ2MS41MDJDMTguMTcwNyA0NjUuMDg4IDUuMzQ3MDggNDU4LjA3OCAxLjc2MTUzIDQ0NS44NDRDLTEuODIzOSA0MzMuNjExIDUuMTg2MzcgNDIwLjc4NyAxNy40MTk3IDQxNy4yMDJMMjE1Ljg3OCAzNTkuMDM1QzI0Ni4yNzcgMzUwLjEyNSAyNDkuNzM5IDMwOC40NDkgMjIxLjIyNiAyOTQuNjQ1TDQ1LjYyOTcgMjA5LjYzNUMtMjAuOTgzNCAxNzcuMzg2IC0xMi43NzcyIDc5Ljk4OTMgNTguMjkyOCA1OS4zNDAyTDI1OS4xNDcgMC45ODE4MTJaIiBmaWxsPSIjRkZGRkZGIi8+Cjwvc3ZnPgo=&logoColor=white)](https://github.com/cagataycali/awesome-strands-agents)

AI agent that tells you who's hiring. Give it a company name, get back open positions with links.

Built with [Strands Agents](https://strandsagents.com) and deployed to Amazon Bedrock AgentCore Runtime. Uses [Tavily](https://www.tavily.com/) web search to find career pages and job boards.

## Quick Start

```bash
# Get API keys: Anthropic (https://console.anthropic.com)
# and Tavily (https://tavily.com, free tier available)

# Run locally
cd agent
echo "ANTHROPIC_API_KEY=sk-ant-xxxxx" > .env
echo "TAVILY_API_KEY=tvly-xxxxx" >> .env
uv sync
uv run --env-file .env python src/agentcore_app.py

# In another terminal window ("sync" waits for the result; omit it for async)
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"company": "Stripe", "title": "Engineer", "sync": true}'

# Put API keys in SSM Parameter Store
aws ssm put-parameter \
  --name "/job-search-agent/anthropic-api-key" \
  --value "sk-ant-xxxxx" \
  --type SecureString
aws ssm put-parameter \
  --name "/job-search-agent/tavily-api-key" \
  --value "tvly-xxxxx" \
  --type SecureString

# Deploy to AWS
cd cdk && npm run cdk:deploy
```

That's it. The agent fetches live job postings, extracts titles and links, and returns structured results.

## What It Does

- Takes company name (+ optional title/location filters)
- Searches career pages and job boards via Tavily API
- Returns hiring status with position details
- Optionally sends email alerts via SNS when companies are hiring
- Scheduled searches via EventBridge for automated monitoring
- Timestamps each search so you know how fresh the results are

**Example:** `{"company": "Stripe", "title": "Engineer"}` → List of engineering roles at Stripe with application links.

## Project Structure

- **[agent/](agent/)** - Python agent code and local development
- **[cdk/](cdk/)** - AWS infrastructure and deployment
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Full deployment guide

## Next Steps

**Want to run it locally?** See [agent/README.md](agent/README.md)

**Want to see how the AWS infra is set up?** See [cdk/README.md](cdk/README.md)

**Ready to deploy to AWS?** See [DEPLOYMENT.md](DEPLOYMENT.md)

**Want a more detailed write up of the background of how this came to be?** Read [this blogpost](https://danielleheberling.xyz/blog/job-search-agent/)
