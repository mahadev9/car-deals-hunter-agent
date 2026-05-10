import logging
import os
import sys
from uuid import uuid4

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.types import Checkpointer

from config import settings
from services.prompt_config import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


async def create_llm_agent(checkpointer: Checkpointer):
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

    logger.info("Initializing LLM agent")

    return create_agent(
        model=settings.llm_client,
        tools=tools,
        name="Car Deals Hunter Agent",
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )


async def invoke_agent(query: str):
    logger.info(f"Invoking agent with query: {query}")

    async with AsyncSqliteSaver.from_conn_string(
        settings.APP_DATABASE_PATH
    ) as checkpointer:
        agent = await create_llm_agent(checkpointer)

        response = await agent.ainvoke(
            query, config={"configurable": {"thread_id": str(uuid4())}}
        )
