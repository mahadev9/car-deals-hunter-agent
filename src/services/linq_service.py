from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal, Optional

from fastmcp import FastMCP
from linq import AsyncLinqAPIV3
from linq.types import MessageContentParam, ReactionType

from config import settings

mcp = FastMCP(
    name="Linq Messaging Service",
    description="Tools for interacting with the Linq API.",
)


@asynccontextmanager
async def linq_client() -> AsyncIterator[AsyncLinqAPIV3]:
    client = AsyncLinqAPIV3(api_key=settings.LINQ_API_KEY.get_secret_value())
    try:
        yield client
    finally:
        await client.close()


def build_text_message(message: str) -> MessageContentParam:
    return MessageContentParam(parts=[{"type": "text", "value": message}])


async def start_typing_indicator(linq_client: AsyncLinqAPIV3, chat_id: str):
    await linq_client.chats.typing.start(chat_id)


async def stop_typing_indicator(linq_client: AsyncLinqAPIV3, chat_id: str):
    await linq_client.chats.typing.stop(chat_id)


@mcp.tool(name="mark_chat_as_read", description="Mark a chat as read")
async def mark_chat_as_read(chat_id: str):
    async with linq_client() as client:
        await client.chats.mark_as_read(chat_id)


@mcp.tool(name="send_a_message", description="Send a message to a chat")
async def send_a_message(chat_id: str, message: str):
    async with linq_client() as client:
        await start_typing_indicator(client, chat_id)
        try:
            await client.chats.messages.send(
                chat_id, message=build_text_message(message)
            )
        finally:
            await stop_typing_indicator(client, chat_id)


@mcp.tool(name="get_messages_from_a_chat", description="Get messages from a chat")
async def get_messages_from_a_chat(chat_id: str, limit: int = 20):
    async with linq_client() as client:
        return [
            chat_message.model_dump()
            async for chat_message in client.chats.messages.list(chat_id, limit=limit)
        ]


@mcp.tool(
    name="add_or_remove_a_reaction_to_a_message",
    description="Add or remove a reaction to a message",
)
async def add_or_remove_a_reaction_to_a_message(
    message_id: str,
    operation: Literal["add", "remove"],
    reaction_type: ReactionType,
    custom_emoji: Optional[str] = None,
):
    async with linq_client() as client:
        reaction_kwargs = {"operation": operation, "type": reaction_type}
        if custom_emoji is not None:
            reaction_kwargs["custom_emoji"] = custom_emoji

        await client.messages.add_reaction(message_id, **reaction_kwargs)


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
