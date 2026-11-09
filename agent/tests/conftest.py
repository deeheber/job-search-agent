from collections.abc import Iterator
from unittest.mock import AsyncMock, Mock, patch

import pytest
from strands import tool
from strands.tools.mcp import MCPClient


@pytest.fixture
def tavily_client() -> Iterator[Mock]:
    @tool(name="tavily_search")
    def search(query: str) -> str:
        """Search for jobs."""
        return "No jobs found"

    @tool(name="tavily_extract")
    def extract(urls: list[str]) -> str:
        """Extract career page content."""
        return "No jobs found"

    client = Mock(spec=MCPClient)
    client.load_tools = AsyncMock(return_value=[search, extract])
    with patch("src.agentcore_app.get_tavily_client", return_value=client):
        yield client
