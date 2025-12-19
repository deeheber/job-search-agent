"""Tests for the agent."""

import os
from unittest.mock import patch

from src.agentcore_app import DEFAULT_MODEL_ID, get_agent, get_model_id


def test_agent_has_tools() -> None:
    """Test agent has expected tools registered."""
    agent = get_agent()
    tool_names = agent.tool_names
    assert "calculator" in tool_names
    assert "current_time" in tool_names
    assert "letter_counter" in tool_names


def test_get_model_id_fallback() -> None:
    """Test get_model_id returns the default when environment variable is not set."""
    with patch.dict(os.environ, {}, clear=True):
        model_id = get_model_id()
        assert model_id == DEFAULT_MODEL_ID
