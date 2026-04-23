# Agent Development

The Python side of the job search agent. This is where the AI magic happens.

## Running Locally

```bash
# First time setup
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Add your Tavily API key (get one at tavily.com)
echo "TAVILY_API_KEY=tvly-xxxxx" > .env

# Start the agent
python src/agentcore_app.py
```

The agent starts on `localhost:8080`. Test it with:

```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"company": "Stripe", "title": "Engineer"}'
```

## How It Works

The agent uses community tools from `strands-agents-tools`:

- **tavily_search** - Searches the web for career pages and job listings
- **http_request** - Fetches specific URLs found by search
- **current_time** - Timestamps search results

When you send a company name, the agent searches for career pages, fetches the content, and extracts job information.

## Configuration

Copy `.env.example` to `.env` and add your Tavily API key:

```bash
cp .env.example .env
# Edit .env and set TAVILY_API_KEY=tvly-xxxxx
```

The Tavily API key is required for web search. Get one at [tavily.com](https://tavily.com).

For AWS deployment, the key is stored in SSM Parameter Store instead (see [DEPLOYMENT.md](../DEPLOYMENT.md)).

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
./quality-check.sh    # Run all checks (mypy, ruff, black, pytest)
pytest                # Just the tests
```

The quality check script auto-fixes most issues. Run it before committing.

## Adding Custom Tools

Right now we're using community tools, but you can add custom ones in `src/tools/`:

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
