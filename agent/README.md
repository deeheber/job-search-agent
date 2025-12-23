# Job Search Agent

Python 3.13 agent that monitors company hiring status using `http_request` and `current_time` tools.

## Quick Start

```bash
python3.13 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
python src/agentcore_app.py

# Test with: "Is Panic Inc. hiring software engineers?"
```

## Configuration

**Environment Variables**: The agent automatically loads environment variables from a `.env` file when running locally (requires `python-dotenv` from dev dependencies).

```bash
# Copy the example and customize
cp .env.example .env

# Edit .env file
BEDROCK_MODEL_ID=your-preferred-model-id
LOG_LEVEL=DEBUG
```

**Model**: Set `BEDROCK_MODEL_ID` environment variable (see `DEFAULT_MODEL_ID` in `src/agentcore_app.py` for current default)

**Available Models**: See [AWS Bedrock Model IDs documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html)

## Job Search Features

**Current Tools:**

- `http_request` - Fetch company career pages and job board APIs
- `current_time` - Track job posting dates and search timestamps

**Sample Queries:**

- "Is [Company Name] hiring software engineers?"
- "What positions are available at [Company Name]?"
- "Check if [Company Name] has any open roles"

**Response Format:**

```json
{
  "status": "success",
  "response": "Company hiring status and details",
  "jobs": [
    {
      "title": "Software Engineer",
      "link": "https://company.com/careers/123",
      "posted_date": "2024-01-15"
    }
  ]
}
```

## Development

```bash
./quality-check.sh    # All quality checks (recommended)
pytest               # Tests only
```

See [DEPLOYMENT.md](../DEPLOYMENT.md) for cloud deployment.
