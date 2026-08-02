# Agent Development

The Python side of the job search agent.

## Running Locally

```bash
# First time setup
uv sync

# Add your API keys (console.anthropic.com and tavily.com)
echo "ANTHROPIC_API_KEY=sk-ant-xxxxx" > .env
echo "TAVILY_API_KEY=tvly-xxxxx" >> .env

# Start the agent
uv run --env-file .env python src/agentcore_app.py
```

The agent starts on `localhost:8080`. Test it with:

```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"company": "Stripe", "title": "Engineer", "sync": true}'
```

`"sync": true` returns the full result. Without it the agent replies `{"status": "accepted"}` immediately and logs the result when done. Scheduled invokes use this mode, since EventBridge Scheduler's call times out after ~30s.

## How It Works

The agent uses community tools from `strands-agents-tools`, plus one custom tool:

- **tavily_search** - Searches the web for career pages and job listings
- **tavily_extract** - Fetches page content from URLs found by search
- **current_time** - Timestamps search results
- **send_job_alert** - Custom tool in `src/tools/` that publishes SNS notifications (loaded when `SNS_TOPIC_ARN` is set)

When you send a company name, the agent searches for career pages, fetches the content, and extracts job information. Pages are fetched server-side by Tavily, so the runtime never makes arbitrary outbound requests.

## Configuration

Copy `.env.example` to `.env` and add your API keys:

```bash
cp .env.example .env
```

The Anthropic API key powers the model (or set `MODEL_PROVIDER=bedrock` to use Amazon Bedrock via IAM instead). The Tavily API key is required for web search.

For AWS deployment, the keys are stored in SSM Parameter Store instead (see [DEPLOYMENT.md](../DEPLOYMENT.md)).

## Input Format

Send JSON with a company name and optional filters:

```json
{
  "company": "Netflix",
  "title": "Data Scientist",
  "location": "remote"
}
```

The agent returns hiring status, position titles, and application links.

## Development Workflow

```bash
./quality-check.sh    # Run all checks (pytest, mypy, ruff, black)
uv run pytest         # Just the tests
```

The quality check script auto-fixes most issues. Run it before committing.

## Adding Custom Tools

Custom tools live in `src/tools/` (see `sns_tools.py`). To add one:

```python
from strands import tool

@tool
def parse_greenhouse_api(company_id: str) -> dict:
    """Fetch jobs from Greenhouse API."""
    # Your implementation
    return {"jobs": [...]}
```

Export it in `src/tools/__init__.py` and add to the agent's tool list.

## Next Steps

Ready to deploy? Head to [../DEPLOYMENT.md](../DEPLOYMENT.md) for AWS setup.
