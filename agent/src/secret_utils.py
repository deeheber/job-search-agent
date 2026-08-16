"""Secrets management utilities for local and AWS environments."""

import logging
import os
from functools import lru_cache

logger = logging.getLogger(__name__)

# Default SSM parameter names (created out-of-band, never by the CDK stack;
# they must exist by the time the agent is invoked)
DEFAULT_TAVILY_SSM_PARAMETER = "/job-search-agent/tavily-api-key"
DEFAULT_ANTHROPIC_SSM_PARAMETER = "/job-search-agent/anthropic-api-key"


def is_aws_environment() -> bool:
    """Detect AWS via env vars set by AgentCore Runtime and other AWS compute services."""
    aws_indicators = [
        "AWS_EXECUTION_ENV",
        "AWS_LAMBDA_FUNCTION_NAME",
        "ECS_CONTAINER_METADATA_URI",
        "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI",
    ]
    return any(os.environ.get(var) for var in aws_indicators)


def get_tavily_api_key() -> str:
    """Retrieve the Tavily API key (env var locally, SSM in AWS)."""
    return _get_api_key(
        env_var="TAVILY_API_KEY",
        ssm_param_env_var="TAVILY_API_KEY_SSM_PARAMETER",
        default_parameter=DEFAULT_TAVILY_SSM_PARAMETER,
    )


def get_anthropic_api_key() -> str:
    """Retrieve the Anthropic API key (env var locally, SSM in AWS)."""
    return _get_api_key(
        env_var="ANTHROPIC_API_KEY",
        ssm_param_env_var="ANTHROPIC_API_KEY_SSM_PARAMETER",
        default_parameter=DEFAULT_ANTHROPIC_SSM_PARAMETER,
    )


def _get_api_key(env_var: str, ssm_param_env_var: str, default_parameter: str) -> str:
    """
    Retrieve an API key: env var first when running locally, SSM in AWS.

    Raises:
        ValueError: If the API key cannot be retrieved
    """
    if not is_aws_environment():
        env_key = os.environ.get(env_var)
        if env_key:
            logger.info(f"Using {env_var} from environment variable")
            return env_key
        logger.info(f"{env_var} not in environment, attempting SSM...")

    parameter_name = os.environ.get(ssm_param_env_var, default_parameter)
    return _get_from_ssm(parameter_name)


@lru_cache(maxsize=8)
def _get_from_ssm(parameter_name: str) -> str:
    """Fetch a secret from SSM Parameter Store (cached per parameter name)."""
    # Local: imported here so env-var runs never pay boto3's import cost
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError

    logger.info(f"Fetching API key from SSM Parameter: {parameter_name}")

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
