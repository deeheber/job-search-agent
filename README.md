# Job Search Agent

AI agent that tells you who's hiring. Give it a company name, get back open positions with links.

Built with [Strands Agents](https://strandsagents.com) and deployed to Amazon Bedrock AgentCore Runtime. Uses [Tavily](https://www.tavily.com/) web search to find career pages and job boards.

> **Note:** This project was started before my current employment as a learning exercise. I'm completing it to finish what I started, not as an indication of active job searching.

## Quick Start

```bash
# Get a Tavily API key (free tier available)
# Sign up at https://tavily.com

# Run locally
cd agent
echo "TAVILY_API_KEY=your_key_here" > .env
python src/agentcore_app.py

# In another terminal window
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"company": "Stripe", "title": "Engineer"}'

# Put Tavily API key in SSM Parameter Store
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
- Tracks when jobs were posted

**Example:** `{"company": "Stripe", "title": "Engineer"}` → List of engineering roles at Stripe with application links.

## Project Structure

- **[agent/](agent/)** - Python agent code and local development
- **[cdk/](cdk/)** - AWS infrastructure and deployment
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Full deployment guide

## Next Steps

**Want to run it locally?** See [agent/README.md](agent/README.md)

**Want to see how the AWS infra is set up?** See [cdk/README.md](cdk/README.md)

**Ready to deploy to AWS?** See [DEPLOYMENT.md](DEPLOYMENT.md)
