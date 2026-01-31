# Agent Development

The Python side of the job search agent. This is where the AI magic happens.

## Running Locally

```bash
# First time setup
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

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

The agent uses two community tools from `strands-agents-tools`:

- **http_request** - Fetches company career pages and job board APIs
- **current_time** - Timestamps job postings and search results

When you send a company name, the agent figures out where to look, fetches the data, and extracts job information. It's basically a smart web scraper that knows how to find and parse job listings.

## Configuration

Copy `.env.example` to `.env` and customize:

```bash
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0
LOG_LEVEL=INFO
```

The agent loads these automatically when running locally. See [AWS Bedrock Model IDs](https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html) for available models.

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
from strands.agent import tool

@tool
def parse_greenhouse_api(company_id: str) -> dict:
    """Fetch jobs from Greenhouse API."""
    # Your implementation
    return {"jobs": [...]}
```

Export it in `src/tools/__init__.py` and add to the agent's tool list.

## Next Steps

Ready to deploy? Head to [../DEPLOYMENT.md](../DEPLOYMENT.md) for AWS setup.
