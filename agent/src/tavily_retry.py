import asyncio
import logging
import random

from strands import Agent
from strands.hooks import AfterToolCallEvent, BeforeToolCallEvent
from strands.plugins import Plugin

TAVILY_TOOL_NAMES = {"tavily_search", "tavily_extract"}
RETRY_DELAYS = (30, 60)
EXHAUSTED_MESSAGE = (
    "Tavily rate-limit retries exhausted. Stop calling Tavily for this search. "
    "Report the search as incomplete, not as finding no matching jobs."
)
logger = logging.getLogger(__name__)


class TavilyRetry(Plugin):
    """Use with sequential tool execution and a fresh instance for each search."""

    name = "tavily-retry"

    def __init__(self) -> None:
        self.retries = 0
        self.exhausted = False
        super().__init__()

    def init_agent(self, agent: Agent) -> None:
        agent.hooks.add_callback(BeforeToolCallEvent, self.before_tool)
        agent.hooks.add_callback(AfterToolCallEvent, self.after_tool)

    def before_tool(self, event: BeforeToolCallEvent) -> None:
        if self.exhausted and event.tool_use["name"] in TAVILY_TOOL_NAMES:
            event.cancel_tool = EXHAUSTED_MESSAGE

    async def after_tool(self, event: AfterToolCallEvent) -> None:
        if event.tool_use["name"] not in TAVILY_TOOL_NAMES:
            return
        payload = event.result.get("structuredContent")
        # Tavily currently returns these errors with MCP isError=False.
        if not isinstance(payload, dict) or payload.get("status") != 429:
            return
        event.result["status"] = "error"
        if self.retries == len(RETRY_DELAYS):
            self.exhausted = True
            event.result["content"].append({"text": EXHAUSTED_MESSAGE})
            logger.warning("Tavily rate-limit retry budget exhausted")
            return
        delay = RETRY_DELAYS[self.retries] + random.uniform(0, 5)
        self.retries += 1
        logger.warning(
            "Tavily rate-limited; retry %d/%d in %.2f seconds",
            self.retries,
            len(RETRY_DELAYS),
            delay,
        )
        await asyncio.sleep(delay)
        event.retry = True
