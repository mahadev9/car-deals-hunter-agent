import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/linq", tags=["linq"])


@router.post("/webhook")
async def handle_linq_webhook():
    logger.info("Received a webhook from LINQ")
    pass
