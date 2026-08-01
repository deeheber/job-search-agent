# Contributing to Job Search Agent

How to set up a development environment and get changes merged.

## Getting Started

### Prerequisites

- **Python 3.14** (see `.python-version`)
- **[uv](https://docs.astral.sh/uv/)** for Python package management
- **Node.js 24** (see `.nvmrc`)
- **Docker** (for deployment)
- **AWS CLI** configured with appropriate permissions
- **Tavily API key** (sign up at [tavily.com](https://tavily.com) - free tier available)
- **Anthropic API key** (sign up at [console.anthropic.com](https://console.anthropic.com)), or Bedrock model access in your AWS account when using `MODEL_PROVIDER=bedrock`

### Initial Setup

1. **Fork and clone the repository**

   ```bash
   git clone https://github.com/your-username/job-search-agent.git
   cd job-search-agent
   ```

2. **Set up the Python environment**

   ```bash
   cd agent
   uv sync
   ```

3. **Set up the CDK environment**

   ```bash
   cd ../cdk
   npm install
   ```

4. **Configure environment variables**
   ```bash
   cd ../agent
   cp .env.example .env
   # Edit .env and add your Tavily and Anthropic API keys
   ```

## Development Workflow

### Python Agent Development

**Running the agent locally:**

```bash
cd agent
uv run --env-file .env python src/agentcore_app.py

# Test with input: {"company": "Panic Inc.", "title": "Software Engineer"}
```

**Quality checks (recommended before committing):**

```bash
./quality-check.sh  # Runs all checks with auto-fixes
```

**Manual quality validation:**

```bash
uv run pytest && uv run mypy src/ && uv run ruff check --fix . && uv run black .
```

### CDK Infrastructure Development

**Building and testing:**

```bash
cd cdk
npm run build
npm test
```

**Linting and formatting:**

```bash
npm run lint
npm run format
```

**Deploying to AWS:**

```bash
npm run cdk:synth    # Generate CloudFormation
npm run cdk:deploy   # Deploy to AWS
```

## Code Standards

### Python Code Style

- **Line length**: 100 characters
- **Formatter**: Black
- **Linter**: Ruff with auto-fix enabled
- **Type checker**: mypy in strict mode (`src/`)
- **Testing**: pytest

### TypeScript Code Style

- **Formatter**: Prettier
- **Linter**: ESLint
- **Testing**: Vitest with snapshot testing
- **Imports**: Use explicit imports, avoid wildcards

**Good TypeScript imports:**

```typescript
// ✅ Good
import { Stack, StackProps, CfnOutput, Duration } from 'aws-cdk-lib'
import { Runtime, AgentRuntimeArtifact } from 'aws-cdk-lib/aws-bedrockagentcore'

// ❌ Avoid
import * as cdk from 'aws-cdk-lib'
```

## Project Structure

### Adding New Job Search Tools

1. **Create tool file** in `agent/src/tools/` (see `sns_tools.py` for an existing example)
2. **Implement with `@tool` decorator** and proper type hints for job search functionality
3. **Export in `__init__.py`**
4. **Add tests** in `agent/tests/test_tools/`

Example job search tool structure:

```python
from strands import tool

@tool
def search_job_board(company_name: str, position_type: str) -> dict:
    """Search job board API for company positions."""
    return {
        "company": company_name,
        "jobs": [{"title": "...", "link": "...", "posted_date": "..."}]
    }
```

### Current Tool Usage

The agent uses community tools from `strands-agents-tools`, plus one custom tool:

- `tavily_search` - For searching the web for career pages and job listings
- `tavily_extract` - For fetching page content from URLs found by search
- `current_time` - For timestamping search results
- `send_job_alert` - Custom tool in `agent/src/tools/sns_tools.py` that publishes SNS notifications (conditionally loaded when `SNS_TOPIC_ARN` is set)

### Testing Guidelines

**Python tests:**

- Mirror source structure in `tests/` directory
- Test both success and error cases
- Test this project's logic, not framework behavior — skip tests that only restate constants or assert things the language/CDK guarantees

**CDK tests:**

- Use Vitest with snapshot testing
- Test IAM policies, resource configurations, and security settings
- Update snapshots when infrastructure changes are intentional

## Contribution Process

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Follow the code standards outlined above
- Add tests for new functionality
- Update documentation as needed

### 3. Run Quality Checks

**For Python changes:**

```bash
cd agent
./quality-check.sh
```

**For CDK changes:**

```bash
cd cdk
npm run build && npm test && npm run lint
```

### 4. Commit Your Changes

Write commit messages as short plain sentences describing the change, e.g. "Add async invoke path for eventbridge universal target".

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Create a pull request with:

- Clear description of changes
- Reference to any related issues
- Screenshots/examples if applicable

## CI/CD Pipeline

Our GitHub Actions workflows will automatically:

**Agent CI (`agent-ci.yml`):**

- Run pytest
- Type check with mypy
- Lint with ruff
- Format check with black

**CDK CI/CD (`cdk-ci-cd.yml`):**

- Build TypeScript
- Run Vitest tests
- Lint with ESLint
- Format check with Prettier
- Run `cdk synth`, then deploy to AWS on push to main

All checks must pass before merging.

## Community Tools

We use `strands-agents-tools` for common functionality:

```python
from strands_tools import current_time
from strands_tools.tavily import tavily_extract, tavily_search
```

When adding tools, consider if they should be:

- **Custom tools** (domain-specific to your use case)
- **Community contributions** (general-purpose, consider contributing upstream)

## Getting Help

- **Issues**: Create GitHub issues for bugs, feature requests, or questions
- **Documentation**: Check README.md and DEPLOYMENT.md for guidance

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Follow our coding standards consistently
