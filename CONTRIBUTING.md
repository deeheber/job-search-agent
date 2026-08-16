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
./quality-check.sh  # pytest, mypy, ruff, black — with auto-fixes
```

### CDK Infrastructure Development

```bash
cd cdk
npm run build
npm test          # Vitest, including snapshots
npm run fix       # Auto-fix ESLint and Prettier
npm run check     # CI validation, makes no changes
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

See [agent/README.md](agent/README.md#adding-custom-tools).

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
npm run fix && npm run build && npm test && npm run check
```

### 3. Commit Your Changes

Write commit messages as short plain sentences describing the change, e.g. "Add async invoke path for eventbridge universal target".

### 4. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

## CI/CD Pipeline

`agent-ci.yml` and `cdk-ci-cd.yml` run the same checks as above on every PR, and `cdk-ci-cd.yml` deploys to AWS on push to main (see [CI/CD with GitHub Actions](DEPLOYMENT.md#cicd-with-github-actions) for the setup and configuration variables). All checks must pass before merging.
