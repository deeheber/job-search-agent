"""Secrets management utilities for local and AWS environments."""

import logging
import os
from functools import lru_cache

logger = logging.getLogger(__name__)

# Default SSM parameter name for Tavily API key
DEFAULT_TAVILY_SSM_PARAMETER = "/job-search-agent/tavily-api-key"


def is_aws_environment() -> bool:
    """
    Detect if running in AWS environment.

    AgentCore Runtime and other AWS compute services set environment variables
    that indicate we're running in AWS.
    """
    aws_indicators = [
        "AWS_EXECUTION_ENV",
        "AWS_LAMBDA_FUNCTION_NAME",
        "ECS_CONTAINER_METADATA_URI",
        "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI",
    ]
    return any(os.environ.get(var) for var in aws_indicators)


def get_tavily_api_key() -> str:
    """
    Retrieve the Tavily API key from the appropriate source.

    - AWS deployment: Fetches from SSM Parameter Store (cached)
    - Local development: Checks env var first, then falls back to SSM

    Returns:
        str: The Tavily API key

    Raises:
        ValueError: If the API key cannot be retrieved
    """
    if not is_aws_environment():
        env_key = os.environ.get("TAVILY_API_KEY")
        if env_key:
            logger.info("Using TAVILY_API_KEY from environment variable")
            return env_key
        logger.info("TAVILY_API_KEY not in environment, attempting SSM...")

    return _get_from_ssm()


@lru_cache(maxsize=1)
def _get_from_ssm() -> str:
    """Fetch the Tavily API key from SSM Parameter Store (cached)."""
    import boto3  # type: ignore[import-untyped]
    from botocore.exceptions import ClientError, NoCredentialsError  # type: ignore[import-untyped]

    parameter_name = os.environ.get(
        "TAVILY_API_KEY_SSM_PARAMETER",
        DEFAULT_TAVILY_SSM_PARAMETER,
    )

    logger.info(f"Fetching Tavily API key from SSM Parameter: {parameter_name}")

    try:
        ssm_client = boto3.client("ssm")
        response = ssm_client.get_parameter(
            Name=parameter_name,
            WithDecryption=True,
        )
        return str(response["Parameter"]["Value"])
    except NoCredentialsError as e:
        raise ValueError(
            "AWS credentials not configured. "
            "Run 'aws configure' or set AWS environment variables."
        ) from e
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ParameterNotFound":
            raise ValueError(
                f"SSM Parameter '{parameter_name}' not found. Create it with:\n"
                f"  aws ssm put-parameter --name '{parameter_name}' "
                "--value 'your-api-key' --type SecureString"
            ) from e
        if error_code == "AccessDeniedException":
            raise ValueError(
                f"Access denied to SSM Parameter '{parameter_name}'. "
                "Check IAM permissions for ssm:GetParameter."
            ) from e
        raise ValueError(f"Failed to retrieve SSM parameter: {e}") from e


def clear_ssm_cache() -> None:
    """Clear the SSM cache."""
    _get_from_ssm.cache_clear()
