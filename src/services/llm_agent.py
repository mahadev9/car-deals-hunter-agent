from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
import os
import sys
from config import settings


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
    )
