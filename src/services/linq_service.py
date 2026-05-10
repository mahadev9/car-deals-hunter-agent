import hashlib
import hmac
import logging
from typing import Any, Dict

from config import settings
from models.webhook_event_model import WebhookEvent, WebhookEventHeaders
from services.linq_event_handlers import EVENT_HANDLERS
from services.webhook_events import is_duplicate_event

logger = logging.getLogger(__name__)


class WebhookSignatureError(Exception):
    """Raised when webhook signature verification fails."""

    pass


def verify_signature(raw_body: bytes, timestamp: str, signature: str) -> None:
    """Verify the webhook signature using HMAC-SHA256.

    Args:
        raw_body: Raw request body bytes
        timestamp: X-Webhook-Timestamp header value
        signature: X-Webhook-Signature header value

    Raises:
        WebhookSignatureError: If signature verification fails
    """
    secret = settings.LINQ_SIGNING_SECRET.get_secret_value()
    message = f"{timestamp}.{raw_body.decode('utf-8')}"

    expected = hmac.new(
        secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    # Use constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(expected, signature):
        raise WebhookSignatureError("Invalid webhook signature")


async def process_webhook_event(
    payload: WebhookEvent,
    headers: WebhookEventHeaders,
) -> Dict[str, Any]:
    """Process a webhook event (deduplication + routing + handling).

    Args:
        payload (WebhookEvent): Parsed webhook payload
        headers (WebhookEventHeaders): Parsed webhook headers

    Returns:
        Dict[str, Any]: Result of processing (e.g. {"status": "ok"})

    Raises:
        Exception: Re-raises handler exceptions for upstream logging
    """

    # Check for duplicates
    if is_duplicate_event(payload.event_id, headers.event_type):
        logger.info(f"Ignoring duplicate event: {payload.event_id}")
        return {"status": "ok", "duplicate": True}

    # Log webhook received
    logger.info(
        f"Webhook received: {headers.event_type} (subscription: {headers.subscription_id}, "
        f"event_id: {payload.event_id}, timestamp: {headers.timestamp})"
    )

    # Get event handler
    handler = EVENT_HANDLERS.get(headers.event_type)
    if not handler:
        logger.warning(f"No handler registered for event type: {headers.event_type}")
        return {"status": "ok", "unhandled_event_type": True}

    # Route to handler
    await handler(payload)

    return {"status": "ok"}
