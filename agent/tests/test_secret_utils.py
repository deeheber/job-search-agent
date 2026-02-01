"""Tests for secret_utils module."""

import os
from unittest.mock import patch

import pytest

from src.secret_utils import clear_ssm_cache, get_tavily_api_key


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear SSM cache before each test."""
    clear_ssm_cache()
    yield
    clear_ssm_cache()


def test_aws_environment_uses_ssm_directly():
    """In AWS, should fetch from SSM without checking env var."""
    with (
        patch("src.secret_utils.is_aws_environment", return_value=True),
        patch("src.secret_utils._get_from_ssm", return_value="ssm-key") as mock_ssm,
    ):
        result = get_tavily_api_key()

        assert result == "ssm-key"
        mock_ssm.assert_called_once()


def test_local_uses_env_var_when_set():
    """Locally, should use env var if available without calling SSM."""
    with (
        patch("src.secret_utils.is_aws_environment", return_value=False),
        patch.dict(os.environ, {"TAVILY_API_KEY": "env-key"}),
        patch("src.secret_utils._get_from_ssm") as mock_ssm,
    ):
        result = get_tavily_api_key()

        assert result == "env-key"
        mock_ssm.assert_not_called()


def test_local_falls_back_to_ssm():
    """Locally without env var, should try SSM."""
    with (
        patch("src.secret_utils.is_aws_environment", return_value=False),
        patch.dict(os.environ, {}, clear=True),
        patch("src.secret_utils._get_from_ssm", return_value="ssm-fallback-key"),
    ):
        os.environ.pop("TAVILY_API_KEY", None)
        result = get_tavily_api_key()

        assert result == "ssm-fallback-key"


def test_local_error_when_both_fail():
    """Locally without env var and SSM fails, should propagate SSM error."""
    with (
        patch("src.secret_utils.is_aws_environment", return_value=False),
        patch.dict(os.environ, {}, clear=True),
        patch("src.secret_utils._get_from_ssm", side_effect=ValueError("Parameter not found")),
    ):
        os.environ.pop("TAVILY_API_KEY", None)

        with pytest.raises(ValueError) as exc_info:
            get_tavily_api_key()

        assert "Parameter not found" in str(exc_info.value)
