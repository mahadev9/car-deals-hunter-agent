import logging

import uvicorn
from fastapi import FastAPI

from config import settings
from logger import LOGGING_CONFIG, bootstrap_logging
from routes.linq_webhook import router as linq_webhook_router

bootstrap_logging()
logger = logging.getLogger(__name__)


def lifespan(app: FastAPI):
    logger.info("Starting up the Car Deals Hunter Agent...")
    yield
    logger.info("Shutting down the Car Deals Hunter Agent...")


app = FastAPI(
    title="Car Deals Hunter Agent",
    description="An autonomous agent that hunts for the best car deals online and notifies users via LINQ.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router=linq_webhook_router, prefix="/api")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.APP_PORT,
        reload=settings.ENV == "dev",
        log_config=LOGGING_CONFIG,
    )
