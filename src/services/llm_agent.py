import asyncio
import logging
from uuid import uuid4

from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.types import Checkpointer
from langchain_mcp_adapters.client import MultiServerMCPClient

from config import settings
from services.api_errors import (
    APIError,
    LLMAPIError,
    MCPServerError,
    TimeoutError as APITimeoutError,
    retry_with_exponential_backoff,
)
from services.prompt_config import SYSTEM_PROMPT

logger = logging.getLogger("car-deals-hunter")


async def _create_mcp_client_with_timeout():
    """Create MCP client with timeout handling."""
    try:
        client = MultiServerMCPClient(
            connections={
                "car-deals-hunter": {
                    "transport": "streamable-http",
                    "url": "http://localhost:8010/mcp",
                }
            }
        )
        tools = await asyncio.wait_for(
            client.get_tools(), timeout=settings.MCP_SERVER_TIMEOUT
        )
        return client, tools
    except asyncio.TimeoutError as e:
        logger.error("MCP server connection timed out")
        raise MCPServerError("MCP server not responding") from e
    except Exception as e:
        logger.error(f"Failed to connect to MCP server: {str(e)}")
        raise MCPServerError(f"MCP server error: {str(e)}") from e


async def create_llm_agent(checkpointer: Checkpointer):
    """Create LLM agent with error handling for MCP server."""
    try:
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
    except MCPServerError:
        raise
    except Exception as e:
        logger.error(f"Failed to create LLM agent: {str(e)}")
        raise LLMAPIError(f"Agent creation failed: {str(e)}") from e


async def _invoke_agent_internal(query: str, checkpointer: Checkpointer):
    """Internal agent invocation with timeout."""
    agent = await create_llm_agent(checkpointer)

    try:
        await asyncio.wait_for(
            agent.ainvoke(
                {"messages": [HumanMessage(content=query)]},
                config={"configurable": {"thread_id": str(uuid4())}},
            ),
            timeout=settings.LLM_INVOCATION_TIMEOUT,
        )
        logger.info("Agent invocation completed successfully")
    except asyncio.TimeoutError as e:
        logger.error(
            f"Agent invocation timed out after {settings.LLM_INVOCATION_TIMEOUT}s: {str(e)}"
        )
        raise APITimeoutError(
            f"LLM API call timed out after {settings.LLM_INVOCATION_TIMEOUT}s"
        ) from e
    except Exception as e:
        logger.error(f"Agent invocation failed: {type(e).__name__}: {str(e)}")
        raise LLMAPIError(f"LLM API call failed: {str(e)}") from e


async def invoke_agent(query: str) -> bool:
    """
    Invoke the agent with retry logic and error handling.

    Args:
        query: The user query to process

    Returns:
        bool: True if invocation succeeded, False if it failed

    Raises:
        Logs errors but does not raise to allow background processing to continue
    """
    logger.info(f"Invoking agent with query: {query}")

    try:
        async with AsyncSqliteSaver.from_conn_string(
            settings.CHECKPOINTER_DATABASE_PATH
        ) as checkpointer:
            await retry_with_exponential_backoff(
                _invoke_agent_internal,
                max_retries=settings.LLM_RETRY_MAX_ATTEMPTS - 1,
                initial_delay=settings.LLM_RETRY_INITIAL_DELAY,
                max_delay=settings.LLM_RETRY_MAX_DELAY,
                query=query,
                checkpointer=checkpointer,
            )
        return True

    except APITimeoutError as e:
        logger.error(f"Agent invocation timeout (non-retryable): {str(e)}")
        return False
    except MCPServerError as e:
        logger.error(
            f"MCP server error: {str(e)}. Ensure MCP server is running on http://localhost:8010/mcp"
        )
        return False
    except LLMAPIError as e:
        logger.error(f"LLM API error: {str(e)}")
        return False
    except APIError as e:
        logger.error(f"API error after retries: {str(e)}")
        return False
    except Exception as e:
        logger.error(
            f"Unexpected error during agent invocation: {type(e).__name__}: {str(e)}",
            exc_info=True,
        )
        return False
