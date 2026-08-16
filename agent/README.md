# Agent Development

The Python side of the job search agent.

## Running Locally

```bash
uv sync
cp .env.example .env   # add your Anthropic and Tavily API keys
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

`.env.example` documents every variable. The Anthropic API key powers the model (or set `MODEL_PROVIDER=bedrock` to use Amazon Bedrock via IAM instead). The Tavily API key is required for web search.

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

`src/tools/sns_tools.py` works through every step below. To add your own:

1. Write it in a new module under `src/tools/`, decorated with `@tool` and fully type-hinted. Strands serializes the docstring into the tool schema, so its summary and `Args:` descriptions are what the model reads when deciding to call the tool.
2. Export it from `src/tools/__init__.py` alongside the existing tools.
3. Append it to the `tools` list in `get_agent()` in `agentcore_app.py`.
4. Add tests in `tests/test_tools/`, mirroring `test_sns_tools.py`.

## Next Steps

Ready to deploy? Head to [../DEPLOYMENT.md](../DEPLOYMENT.md) for AWS setup.
