# Technology Stack

## Core Stack

- **Python 3.13** (`.python-version`)
- **Node.js 24** (`.nvmrc`) - For CDK development
- **strands-agents[otel]** (>=1.19.0) - Agent framework with OpenTelemetry
- **strands-agents-tools** (>=0.2.17) - Community tools
- **bedrock-agentcore** (>=1.1.1) - AgentCore SDK
- **aws-opentelemetry-distro** (>=0.14.0) - AWS OpenTelemetry distribution
- **boto3** (>=1.42.9) - AWS SDK for Python
- **pytest, mypy, ruff, black** - Quality assurance tools

## Community Tools

Available from `strands_tools`: `file_read`, `file_write`, `http_request`, `browser`, `python_repl`, `shell`, `calculator`, `current_time`, `generate_image`, etc.

```python
from strands_tools import calculator, current_time, http_request
```

## Commands

**Setup:**

```bash
cd agent
python3.13 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

**Development:**

```bash
python src/agentcore_app.py     # Run locally
./quality-check.sh              # All quality checks (auto-fixes issues)
pytest && mypy src/ && ruff check --fix . && black .  # Manual validation with fixes
```

**Configuration:** All settings in `agent/pyproject.toml` (line length: 100, Python 3.13, strict mode)

## Model Configuration

**BEDROCK_MODEL_ID**: Configure Bedrock model (see `DEFAULT_MODEL_ID` in `agent/src/agentcore_app.py`)
**Examples**: `us.anthropic.claude-3-5-sonnet-20241022-v2:0`, `us.amazon.titan-text-express-v1`
**Local**: Set in `.env` file | **Deploy**: CDK environment variables

## AWS Deployment

**Prerequisites:** Docker running, AWS CLI configured, Bedrock access

**Deploy:**

```bash
cd cdk && npm install && npm run build && cdk deploy
```

**Regions:** Auto-detected from AWS CLI. See [supported regions](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-regions.html)

See `DEPLOYMENT.md` for details.

## CDK Development

**Import Best Practice:** Use explicit imports, avoid wildcards

```typescript
// ✅ Good
import { Stack, StackProps } from "aws-cdk-lib";
import { Function, Runtime } from "aws-cdk-lib/aws-lambda";

// ❌ Avoid
import * as cdk from "aws-cdk-lib";
```

**Commands:**

```bash
cd cdk
npm install && npm run build && npm test    # Build & test
npm run lint && npm run format              # Quality
cdk synth && cdk deploy                     # Deploy
```

**Current Versions:**

- CDK: 2.1033.0
- aws-bedrock-agentcore-alpha: ^2.230.0-alpha.0

## CI/CD

- **agent-ci.yml** - Python testing (pytest, mypy, ruff, black)
- **cdk-ci.yml** - TypeScript testing (Jest, ESLint, Prettier)
- Runs on push/PR to main
