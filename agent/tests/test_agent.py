"""Tests for the agent."""

import os
from unittest.mock import patch

from src.agentcore_app import DEFAULT_MODEL_ID, construct_job_search_prompt, get_agent, get_model_id


def test_agent_has_tools() -> None:
    """Test agent has expected tools registered."""
    with patch("src.agentcore_app.get_tavily_api_key", return_value="mock-api-key"):
        agent = get_agent()
    tool_names = agent.tool_names
    assert "current_time" in tool_names
    assert "http_request" in tool_names
    assert "tavily_search" in tool_names


def test_get_model_id_fallback() -> None:
    """Test get_model_id returns the default when environment variable is not set."""
    with patch.dict(os.environ, {}, clear=True):
        model_id = get_model_id()
        assert model_id == DEFAULT_MODEL_ID


def test_system_prompt_contains_filtering_rules() -> None:
    """Test that system prompt contains strict filtering instructions."""
    from src.agentcore_app import SYSTEM_PROMPT

    # Check for key filtering concepts
    assert "Strict filtering" in SYSTEM_PROMPT
    assert "match ALL user criteria" in SYSTEM_PROMPT
    assert "NEVER construct or invent URLs" in SYSTEM_PROMPT
    assert "No direct link available" in SYSTEM_PROMPT

    # Check for specific role matching examples
    assert "Software Engineer" in SYSTEM_PROMPT
    assert "does NOT match" in SYSTEM_PROMPT


def test_construct_job_search_prompt_company_only() -> None:
    """Test prompt construction with company name only."""
    result = construct_job_search_prompt("Google")
    assert result == "Find jobs at Google."


def test_construct_job_search_prompt_with_all_params() -> None:
    """Test prompt construction with all parameters."""
    result = construct_job_search_prompt("Microsoft", title="Software Engineer", location="remote")
    assert result == "Find jobs at Microsoft. Focus on 'Software Engineer' roles in remote."


def test_system_prompt_uses_search_approach() -> None:
    """Test that system prompt uses tavily_search instead of URL guessing."""
    from src.agentcore_app import SYSTEM_PROMPT

    assert "tavily_search" in SYSTEM_PROMPT
    # Old URL patterns should be removed
    assert "https://careers.COMPANY.com" not in SYSTEM_PROMPT


def test_agent_with_sns_has_use_aws_tool() -> None:
    """Test agent includes use_aws tool when SNS_TOPIC_ARN is configured."""
    with (
        patch("src.agentcore_app.get_tavily_api_key", return_value="mock-api-key"),
        patch.dict(os.environ, {"SNS_TOPIC_ARN": "arn:aws:sns:us-west-2:123456789012:test-topic"}),
    ):
        agent = get_agent()
    assert "use_aws" in agent.tool_names


def test_system_prompt_includes_sns_when_configured() -> None:
    """Test system prompt contains SNS instructions with topic ARN when configured."""
    topic_arn = "arn:aws:sns:us-west-2:123456789012:test-topic"
    with (
        patch("src.agentcore_app.get_tavily_api_key", return_value="mock-api-key"),
        patch.dict(os.environ, {"SNS_TOPIC_ARN": topic_arn}),
    ):
        agent = get_agent()
    assert topic_arn in agent.system_prompt
    assert "sns" in agent.system_prompt.lower()
    assert "publish" in agent.system_prompt.lower()
