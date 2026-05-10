import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal, Optional

from linq import AsyncLinqAPIV3
from linq.types import MessageContentParam, ReactionType

from config import settings

logger = logging.getLogger(__name__)


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


async def mark_chat_as_read(chat_id: str):
    """
    Mark a chat as read.

    Args:
        chat_id (str): The ID of the chat to mark as read.
    """
    logger.info(f"Marking chat {chat_id} as read using tool")
    async with linq_client() as client:
        await client.chats.mark_as_read(chat_id)


async def send_a_message(chat_id: str, message: str):
    """
    Send a message to a chat.

    Args:
        chat_id (str): The ID of the chat to send the message to.
        message (str): The message to send.
    """
    logger.info(f"Sending message to chat {chat_id} using tool")
    async with linq_client() as client:
        await start_typing_indicator(client, chat_id)
        await asyncio.sleep(1)
        try:
            await client.chats.messages.send(
                chat_id, message=build_text_message(message)
            )
        finally:
            await asyncio.sleep(1)
            await stop_typing_indicator(client, chat_id)


async def get_messages_from_a_chat(chat_id: str, limit: int = 20):
    """
    Get messages from a chat.

    Args:
        chat_id (str): The ID of the chat to get messages from.
        limit (int): The maximum number of messages to retrieve.

    Returns:
        List[Dict]: A list of message dictionaries.
    """
    logger.info(f"Getting messages from chat {chat_id} using tool")
    async with linq_client() as client:
        return [
            chat_message.model_dump()
            async for chat_message in client.chats.messages.list(chat_id, limit=limit)
        ]


async def add_or_remove_a_reaction_to_a_message(
    message_id: str,
    operation: Literal["add", "remove"],
    reaction_type: ReactionType,
    custom_emoji: Optional[str] = None,
):
    """
    Add or remove a reaction to a message.

    Args:
        message_id (str): The ID of the message to react to.
        operation (Literal["add", "remove"]): The operation to perform.
        reaction_type (ReactionType): The type of reaction to add or remove.
        custom_emoji (Optional[str]): The custom emoji for the reaction, if applicable.
    """
    logger.info(
        f"{'Adding' if operation == 'add' else 'Removing'} reaction to message {message_id} using tool: type={reaction_type}, custom_emoji={custom_emoji}"
    )
    async with linq_client() as client:
        reaction_kwargs = {"operation": operation, "type": reaction_type}
        if custom_emoji is not None:
            reaction_kwargs["custom_emoji"] = custom_emoji

        await client.messages.add_reaction(message_id, **reaction_kwargs)
