"""AgentCore Runtime wrapper for the Strands agent."""

import logging
import os
from typing import Any

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands_tools import current_time, http_request  # type: ignore[import-untyped]

# Load environment variables from .env file for local development
if os.path.exists(".env"):
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        import warnings

        warnings.warn(
            ".env file found but python-dotenv not installed. "
            "Install with: pip install python-dotenv",
            UserWarning,
            stacklevel=2,
        )

DEFAULT_MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
log_level = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()],
)

logging.getLogger("strands").setLevel(log_level)

app = BedrockAgentCoreApp()

# Disable line length checking for the entire SYSTEM_PROMPT variable
# fmt: off
# ruff: noqa: E501
SYSTEM_PROMPT = """You are a Job Search Agent. Find hiring opportunities at companies.

🚨 CRITICAL: NEVER INVENT JOB URLS 🚨
- DO NOT create any URLs that start with "https://jobs." or "https://careers."
- DO NOT guess application links
- If you cannot find a real link in the HTTP response HTML, you MUST write "No direct link available"
- NEVER construct URLs based on company names or job titles

Process:
1. Use current_time tool
2. Use http_request to fetch company careers page
3. Parse HTML for real job listings and extract ONLY URLs that exist in the response
4. If no results, try LinkedIn or Indeed
5. Apply user filters strictly - ONLY show positions matching ALL criteria

Filtering Rules:
- If user specifies role (e.g., "software engineer"), ONLY show jobs with that role in title
- If user specifies location (e.g., "United States", "US"), ONLY show jobs in that location
- If both specified, job must match BOTH role AND location
- Show maximum 5 positions, even if more found

Response Format:
**Company**: [Name]
**Search Criteria**: [Role/Location filters if specified]
**Hiring Status**: Yes/No/Unknown
**Last Updated**: [Timestamp]

**Positions** (max 5, filtered):
1. **[Job Title]** - [Location]
   - Link: No direct link available

**Additional Results**: [If more than 5 matching positions found]
Found [X] additional matching positions beyond the 5 shown above.

**Search Summary**:
- Checked: [URLs fetched]
- Found: [Number] total positions ([Number] matching filters)

IMPORTANT: Default to "No direct link available" unless you find actual clickable URLs in the HTML."""
# fmt: on


def get_model_id() -> str:
    """
    Get the Bedrock model ID from environment variable or use default.

    Returns:
        str: The model ID to use for the agent
    """
    model_id = os.getenv("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID)
    logging.info(f"Using Bedrock model: {model_id}")
    return model_id


def get_agent() -> Agent:
    """Create and return a Strands agent with configured tools and model."""
    model_id = get_model_id()
    return Agent(model=model_id, tools=[current_time, http_request], system_prompt=SYSTEM_PROMPT)


@app.entrypoint
async def invoke(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Main entrypoint for the agent invocation."""
    try:
        prompt = payload.get("prompt", "Hello!") if payload else "Hello!"

        logging.info(f"AgentCore invocation started with prompt: {prompt}")
        logging.info(f"Payload received: {payload}")

        agent = get_agent()

        response = agent(prompt)
        response_text = response.message["content"][0]["text"]

        logging.info(f"Agent response generated successfully (length: {len(response_text)} chars)")
        logging.info(f"Agent response preview: {response_text[:200]}...")

        result = {"status": "success", "response": response_text}
        logging.info("AgentCore invocation completed successfully")

        return result

    except Exception as e:
        logging.error(f"Error processing request: {e}", exc_info=True)
        logging.error(f"Payload that caused error: {payload}")
        return {"status": "error", "error": "Internal processing error"}


if __name__ == "__main__":
    app.run()
