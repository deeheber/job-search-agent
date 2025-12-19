"""AgentCore Runtime wrapper for the Strands agent."""

import logging
import os
from typing import Any

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands_tools import calculator, current_time, http_request  # type: ignore[import-untyped]

from tools import letter_counter

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
    return Agent(model=model_id, tools=[calculator, current_time, http_request, letter_counter])


@app.entrypoint
async def invoke(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Main entrypoint for the agent invocation."""
    try:
        prompt = payload.get("prompt", "Hello!") if payload else "Hello!"

        logging.info(f"AgentCore invocation started with prompt: {prompt}")
        logging.info(f"Payload received: {payload}")

        agent = get_agent()
        logging.info(
            "Agent created successfully with tools: "
            "calculator, current_time, http_request, letter_counter"
        )

        logging.info("Starting agent execution...")
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
