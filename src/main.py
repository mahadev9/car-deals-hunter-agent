import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from config import settings
from database.core import init_database
from logger import LOGGING_CONFIG, bootstrap_logging
from logger_analytics import configure_analytics_logging
from routes.health import router as health_router
from routes.linq_webhook import router as linq_webhook_router
from services.message_processing_worker import (
    start_message_processing_worker,
    stop_message_processing_worker,
)

bootstrap_logging()
configure_analytics_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up the Car Deals Hunter Agent...")
    os.makedirs(settings.DOCUMENTS_FOLDER_PATH, exist_ok=True)
    init_database()
    worker_task, stop_event = await start_message_processing_worker()
    yield
    await stop_message_processing_worker(worker_task, stop_event)
    logger.info("Shutting down the Car Deals Hunter Agent...")


app = FastAPI(
    title="Car Deals Hunter Agent",
    description="An autonomous agent that hunts for the best car deals online and notifies users via LINQ.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router=linq_webhook_router, prefix="/api")
app.include_router(router=health_router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.APP_PORT,
        reload=settings.ENV == "dev",
        log_config=LOGGING_CONFIG,
    )
