from typing import Literal, Optional

from fastmcp import FastMCP
from linq import AsyncLinqAPIV3
from linq.types import ReactionType

from config import settings

mcp = FastMCP(name="Linq", description="Tools for interacting with the Linq API.")


def get_linq_client() -> AsyncLinqAPIV3:
    return AsyncLinqAPIV3(api_key=settings.LINQ_API_KEY.get_secret_value())


async def start_typing_indicator(linq_client: AsyncLinqAPIV3, chat_id: str):
    await linq_client.chats.typing.start(chat_id)


async def stop_typing_indicator(linq_client: AsyncLinqAPIV3, chat_id: str):
    await linq_client.chats.typing.stop(chat_id)


@mcp.tool(name="mark_chat_as_read", description="Mark a chat as read")
async def mark_chat_as_read(chat_id: str):
    linq_client = get_linq_client()
    await linq_client.chats.mark_as_read(chat_id)


@mcp.tool(name="send_a_message", description="Send a message to a chat")
async def send_a_message(chat_id: str, message: str):
    linq_client = get_linq_client()
    await start_typing_indicator(linq_client, chat_id)
    try:
        await linq_client.chats.messages.send(chat_id, message)
    finally:
        await stop_typing_indicator(linq_client, chat_id)


@mcp.tool(name="get_messages_from_a_chat", description="Get messages from a chat")
async def get_messages_from_a_chat(chat_id: str, limit: int = 20):
    linq_client = get_linq_client()
    messages = await linq_client.chats.messages.list(chat_id, limit=limit)
    return messages


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
    linq_client = get_linq_client()
    await linq_client.messages.add_reaction(
        message_id=message_id,
        operation=operation,
        type=reaction_type,
        custom_emoji=custom_emoji,
    )


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
