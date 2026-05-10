import logging
import os
import sys

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from config import settings
from services.prompt_config import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


async def create_llm_agent():
    client = MultiServerMCPClient(
        {
            "linq": {
                "transport": "stdio",
                "command": sys.executable,
                # Run as a module so package imports resolve correctly
                "args": ["-m", "src.services.linq_service"],
                "env": {"PYTHONPATH": os.path.join(settings.APP_PATH, "src")},
            },
        }
    )

    tools = await client.get_tools()

    if settings.llm_provider == "lmstudio":
        tools.append({"type": "mcp", "server_label": "playwright"})

    return create_agent(
        model=settings.llm_client,
        tools=tools,
        name="Car Deals Hunter Agent",
        system_prompt=SYSTEM_PROMPT,
    )
