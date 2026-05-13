import asyncio
import base64
import logging
import mimetypes
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal, Optional
from uuid import uuid4

import aiofiles
import httpx
from fastmcp import FastMCP
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from linq import AsyncLinqAPIV3
from linq.types import MessageContentParam, ReactionType

from config import settings
from database.core import get_session
from database.models.chat_summary import ChatSummary

logger = logging.getLogger(__name__)

mcp = FastMCP(
    name="Car Deals Hunter Agent Tools",
    instructions="These are tools for Car Deals Hunter Agent to interact with Linq and perform various actions related to chats and messages. Use these tools to read and send messages, manage reactions, perform OCR on images, and maintain chat summaries.",
    version="1.0.0",
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


@mcp.tool(name="mark_chat_as_read", description="Mark a chat as read.")
async def mark_chat_as_read(chat_id: str):
    """
    Mark a chat as read.

    Args:
        chat_id (str): The ID of the chat to mark as read.
    """
    logger.info(f"Marking chat {chat_id} as read using tool")
    async with linq_client() as client:
        await client.chats.mark_as_read(chat_id)


@mcp.tool(name="send_a_message", description="Send a message to a chat.")
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


@mcp.tool(name="get_messages_from_a_chat", description="Get messages from a chat.")
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
    messages = []
    async with linq_client() as client:
        async for chat_message in client.chats.messages.list(chat_id, limit=limit):
            role = "user"
            if chat_message.is_from_me:
                role = "assistant"

            content = ""
            for part in chat_message.parts:
                if part.type == "text":
                    content += f"{part.value}\n"
                elif part.type == "media" and part.mime_type.startswith("image/"):
                    content += f"image: {part.url}\n"
                elif part.type == "link":
                    content += f"link: {part.value}\n"
            messages.append({"role": role, "content": content, "message_id": chat_message.id})
    return messages


@mcp.tool(name="add_or_remove_a_reaction_to_a_message", description="Add or remove a reaction to a message.")
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


async def load_png_as_base64(file_path: str) -> str:
    async with aiofiles.open(file_path, "rb") as image_file:
        encoded_string = base64.b64encode(await image_file.read())
        return encoded_string.decode("utf-8")


@mcp.tool(name="read_image_as_text", description="Read text from an image.")
async def read_image_as_text(image_url: str, prompt: Optional[str] = None) -> str:
    """
    Download an image to documents folder, perform OCR to extract text, and return the extracted text.

    Args:
        image_url (str): The URL of the image to read.
        prompt (Optional[str]): An optional prompt to provide context for the OCR.

    Returns:
        str: The text extracted from the image.
    """

    logger.info("Reading image from URL using tool")
    async with httpx.AsyncClient() as client:
        response = await client.get(image_url)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "").split(";")[0].strip()
        file_extension = mimetypes.guess_extension(content_type) or ".png"
        file_name = f"{uuid4()}{file_extension}"
        file_path = os.path.join(settings.DOCUMENTS_FOLDER_PATH, file_name)

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(response.content)

    if not prompt:
        prompt = "Describe the content of the image in detail."

    screenshot_1_base64 = await load_png_as_base64(file_path)

    logger.info("Performing OCR on the image using LLM")
    chain = settings.llm_client | StrOutputParser()
    return await chain.ainvoke(
        [
            HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{content_type};base64,{screenshot_1_base64}"
                        },
                    },
                ]
            )
        ]
    )


@mcp.tool(name="get_summary_for_chat", description="Fetch the summary for a given chat, if it exists.")
async def get_summary_for_chat(chat_id: str) -> Optional[str]:
    """Fetch the summary for a given chat, if it exists."""

    session = get_session()

    try:
        summary_record = (
            session.query(ChatSummary)
            .filter(ChatSummary.chat_id == chat_id)
            .one_or_none()
        )

        if summary_record:
            return summary_record.summary

        return None
    except Exception as e:
        session.rollback()
        logger.error(
            f"Database error fetching chat summary for chat_id {chat_id}: {str(e)}"
        )
        raise
    finally:
        session.close()


@mcp.tool(name="upsert_summary_for_chat", description="Insert or update the summary for a given chat.")
async def upsert_summary_for_chat(chat_id: str, summary: str) -> None:
    """Insert or update the summary for a given chat."""

    session = get_session()

    try:
        summary_record = (
            session.query(ChatSummary)
            .filter(ChatSummary.chat_id == chat_id)
            .one_or_none()
        )

        if summary_record is None:
            summary_record = ChatSummary(chat_id=chat_id, summary=summary)
            session.add(summary_record)
        else:
            summary_record.summary = summary

        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(
            f"Database error upserting chat summary for chat_id {chat_id}: {str(e)}"
        )
        raise
    finally:
        session.close()


if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8010)
