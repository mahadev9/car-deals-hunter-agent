import logging

from logger import bootstrap_logging

bootstrap_logging()
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Car Deals Hunter Agent is running.")
