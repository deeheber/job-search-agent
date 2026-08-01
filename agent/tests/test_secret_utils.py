"""Tests for secret_utils module."""

import os
from collections.abc import Iterator
from unittest.mock import patch

import pytest

from src.secret_utils import (
    DEFAULT_ANTHROPIC_SSM_PARAMETER,
    DEFAULT_TAVILY_SSM_PARAMETER,
    clear_ssm_cache,
    get_anthropic_api_key,
    get_tavily_api_key,
)


@pytest.fixture(autouse=True)
def clear_cache() -> Iterator[None]:
    """Clear SSM cache before each test."""
    clear_ssm_cache()
    yield
    clear_ssm_cache()


def test_aws_environment_uses_ssm_directly() -> None:
    """In AWS, should fetch from SSM without checking env var."""
    with (
        patch("src.secret_utils.is_aws_environment", return_value=True),
        patch("src.secret_utils._get_from_ssm", return_value="ssm-key") as mock_ssm,
    ):
        result = get_tavily_api_key()

        assert result == "ssm-key"
        mock_ssm.assert_called_once_with(DEFAULT_TAVILY_SSM_PARAMETER)


def test_local_uses_env_var_when_set() -> None:
    """Locally, should use env var if available without calling SSM."""
    with (
        patch("src.secret_utils.is_aws_environment", return_value=False),
        patch.dict(os.environ, {"TAVILY_API_KEY": "env-key"}),
        patch("src.secret_utils._get_from_ssm") as mock_ssm,
    ):
        result = get_tavily_api_key()

        assert result == "env-key"
        mock_ssm.assert_not_called()


def test_local_falls_back_to_ssm() -> None:
    """Locally without env var, should try SSM."""
    with (
        patch("src.secret_utils.is_aws_environment", return_value=False),
        patch.dict(os.environ, {}, clear=True),
        patch("src.secret_utils._get_from_ssm", return_value="ssm-fallback-key"),
    ):
        os.environ.pop("TAVILY_API_KEY", None)
        result = get_tavily_api_key()

        assert result == "ssm-fallback-key"


def test_local_error_when_both_fail() -> None:
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


def test_get_anthropic_api_key_local_env_var() -> None:
    """Locally, should use ANTHROPIC_API_KEY env var without calling SSM."""
    with (
        patch("src.secret_utils.is_aws_environment", return_value=False),
        patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-anthropic-key"}),
        patch("src.secret_utils._get_from_ssm") as mock_ssm,
    ):
        result = get_anthropic_api_key()

        assert result == "env-anthropic-key"
        mock_ssm.assert_not_called()


def test_get_anthropic_api_key_aws_uses_ssm() -> None:
    """In AWS, should fetch the Anthropic key from its own SSM parameter."""
    with (
        patch("src.secret_utils.is_aws_environment", return_value=True),
        patch("src.secret_utils._get_from_ssm", return_value="ssm-anthropic-key") as mock_ssm,
    ):
        result = get_anthropic_api_key()

        assert result == "ssm-anthropic-key"
        mock_ssm.assert_called_once_with(DEFAULT_ANTHROPIC_SSM_PARAMETER)


def test_anthropic_ssm_parameter_env_override() -> None:
    """ANTHROPIC_API_KEY_SSM_PARAMETER should override the default parameter name."""
    with (
        patch("src.secret_utils.is_aws_environment", return_value=True),
        patch.dict(os.environ, {"ANTHROPIC_API_KEY_SSM_PARAMETER": "/custom/param"}),
        patch("src.secret_utils._get_from_ssm", return_value="ssm-key") as mock_ssm,
    ):
        get_anthropic_api_key()

        mock_ssm.assert_called_once_with("/custom/param")


def test_ssm_cache_isolated_per_parameter() -> None:
    """Distinct parameter names are cached independently; repeats hit the cache."""
    from src.secret_utils import _get_from_ssm

    with patch("boto3.client") as mock_boto:
        mock_boto.return_value.get_parameter.side_effect = lambda **kw: {
            "Parameter": {"Value": f"value-for-{kw['Name']}"}
        }
        assert _get_from_ssm("/param/a") == "value-for-/param/a"
        assert _get_from_ssm("/param/b") == "value-for-/param/b"
        assert _get_from_ssm("/param/a") == "value-for-/param/a"

    assert mock_boto.return_value.get_parameter.call_count == 2
