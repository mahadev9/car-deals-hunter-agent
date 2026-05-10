import logging
from uuid import uuid4

from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.types import Checkpointer

from config import settings
from services.chat_summary_tools import get_summary_for_chat, upsert_summary_for_chat
from services.image_tool import read_image_as_text
from services.linq_tools import (
    add_or_remove_a_reaction_to_a_message,
    get_messages_from_a_chat,
    mark_chat_as_read,
    send_a_message,
)
from services.prompt_config import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


async def create_llm_agent(checkpointer: Checkpointer):
    tools = [
        mark_chat_as_read,
        send_a_message,
        get_messages_from_a_chat,
        add_or_remove_a_reaction_to_a_message,
        read_image_as_text,
        get_summary_for_chat,
        upsert_summary_for_chat,
    ]

    if settings.llm_provider == "lmstudio":
        tools.append({"type": "mcp", "server_label": "playwright"})

    if settings.llm_provider == "anthropic":
        tools.append({"type": "web_search_20260209", "name": "web_search"})

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
        settings.APP_DATABASE_PATH
    ) as checkpointer:
        agent = await create_llm_agent(checkpointer)

        await agent.ainvoke(
            {"messages": [HumanMessage(content=query)]},
            config={"configurable": {"thread_id": str(uuid4())}},
        )
        logger.info("agent responding")
