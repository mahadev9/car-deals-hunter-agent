import logging
from uuid import uuid4

from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.types import Checkpointer
from langchain_mcp_adapters.client import MultiServerMCPClient

from config import settings
from services.prompt_config import SYSTEM_PROMPT

logger = logging.getLogger("car-deals-hunter")


async def create_llm_agent(checkpointer: Checkpointer):
    client = MultiServerMCPClient(
        connections={
            "car-deals-hunter": {
                "transport": "streamable-http",
                "url": "http://localhost:8010/mcp",
            }
        }
    )
    tools = await client.get_tools()

    if settings.llm_provider == "lmstudio":
        tools = [
            {"type": "mcp", "server_label": "playwright"},
            {"type": "mcp", "server_label": "car-deals-hunter"},
        ]

    if settings.llm_provider == "anthropic":
        tools.append(
            {
                "type": "web_search_20260209",
                "name": "web_search",
                "allowed_callers": ["direct"],
            }
        )

    if settings.llm_provider == "openai":
        tools.append({"type": "web_search"})

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
        settings.CHECKPOINTER_DATABASE_PATH
    ) as checkpointer:
        agent = await create_llm_agent(checkpointer)

        await agent.ainvoke(
            {"messages": [HumanMessage(content=query)]},
            config={"configurable": {"thread_id": str(uuid4())}},
        )
        logger.info("agent responded")
