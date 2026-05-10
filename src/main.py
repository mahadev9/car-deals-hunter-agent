import asyncio
import logging

from logger import bootstrap_logging

bootstrap_logging()
logger = logging.getLogger(__name__)


async def main():
    logger.info("Car Deals Hunter Agent is running.")


if __name__ == "__main__":
    asyncio.run(main())
