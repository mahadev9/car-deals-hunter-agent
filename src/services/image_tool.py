import base64
import logging
import mimetypes
import os
from typing import Optional
from uuid import uuid4

import aiofiles
import httpx
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser

from config import settings

logger = logging.getLogger(__name__)


async def load_png_as_base64(file_path: str) -> str:
    async with aiofiles.open(file_path, "rb") as image_file:
        encoded_string = base64.b64encode(await image_file.read())
        return encoded_string.decode("utf-8")


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
