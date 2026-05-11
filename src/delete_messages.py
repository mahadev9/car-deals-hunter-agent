from config import settings

import asyncio

from linq import AsyncLinqAPIV3


async def main():
    client = AsyncLinqAPIV3(api_key=settings.LINQ_API_KEY.get_secret_value())

    chats = await client.chats.list_chats()
    async for chat in chats:
        print(f"Deleting messages in chat: {chat.id}")

        messages = await client.chats.messages.list(chat.id)

        async for message in messages:
            print(f"Deleting message: {message.id}")

            await client.messages.delete(message.id)


if __name__ == "__main__":
    asyncio.run(main())
