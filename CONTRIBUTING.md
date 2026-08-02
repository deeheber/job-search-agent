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

Project conventions live in `AGENTS.md`.

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

## Project Structure

### Adding New Job Search Tools

1. **Create tool file** in `agent/src/tools/` (see `sns_tools.py` for an existing example)
2. **Implement with `@tool` decorator** and proper type hints
3. **Export in `__init__.py`**
4. **Add tests** in `agent/tests/test_tools/`

### Testing Guidelines

**Python tests:**

- Mirror source structure in `tests/` directory
- Test both success and error cases
- Test this project's logic, not framework behavior; skip tests that only restate constants or assert things the language/CDK guarantees

**CDK tests:**

- Use Vitest with snapshot testing
- Test IAM policies, resource configurations, and security settings
- Update snapshots when infrastructure changes are intentional

## Contribution Process

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Run Quality Checks

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

### 3. Commit Your Changes

Write commit messages as short plain sentences describing the change, e.g. "Add async invoke path for eventbridge universal target".

### 4. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

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

We use `strands-agents-tools` for common functionality. When adding tools, consider if they should be:

- **Custom tools** (domain-specific to your use case)
- **Community contributions** (general-purpose, consider contributing upstream)

## Getting Help

- **Issues**: Create GitHub issues for bugs, feature requests, or questions

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
