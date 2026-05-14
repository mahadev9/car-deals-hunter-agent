import logging
from typing import Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from models.webhook_event_model import WebhookEvent, WebhookEventHeaders
from services.linq_service import (
    WebhookSignatureError,
    process_webhook_event,
    verify_signature,
)

logger = logging.getLogger("car-deals-hunter")

router = APIRouter(prefix="/linq", tags=["linq"])


async def verify_webhook_signature_dependency(
    request: Request,
) -> Tuple[WebhookEvent, WebhookEventHeaders]:
    """
    FastAPI dependency to verify webhook signature and parse payload.

    This dependency:
    1. Extracts and validates required headers
    2. Verifies the HMAC-SHA256 signature
    3. Parses and returns the webhook payload

    Args:
        request: FastAPI request object

    Returns:
        Tuple[WebhookEvent, WebhookEventHeaders]

    Raises:
        HTTPException: If headers are missing, signature is invalid, or JSON is malformed
    """
    # Extract headers
    timestamp = request.headers.get("X-Webhook-Timestamp")
    signature = request.headers.get("X-Webhook-Signature")
    event_type = request.headers.get("X-Webhook-Event")
    subscription_id = request.headers.get("X-Webhook-Subscription-ID")

    # Validate headers
    if not all([timestamp, signature, event_type, subscription_id]):
        logger.error("Missing required webhook headers")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required webhook headers",
        )

    # Get raw body
    raw_body = await request.body()

    # Verify signature
    try:
        verify_signature(raw_body, timestamp, signature)
    except WebhookSignatureError as e:
        logger.error(f"Webhook signature verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature"
        )

    payload = WebhookEvent.model_validate_json(raw_body.decode("utf-8"))

    headers = WebhookEventHeaders(
        timestamp=timestamp,
        event_type=event_type,
        subscription_id=subscription_id,
    )

    return payload, headers


@router.post("/webhook")
async def handle_linq_webhook(
    verified_data: Tuple[WebhookEvent, WebhookEventHeaders] = Depends(
        verify_webhook_signature_dependency
    ),
) -> JSONResponse:
    """
    Handle Linq webhook events.

    This endpoint:
    1. Verifies webhook signature using the dependency
    2. Delegates to service for event processing
    3. Returns 200 for idempotency

    Args:
        verified_data (Tuple[WebhookEvent, WebhookEventHeaders]): Data returned from signature verification dependency

    Returns:
        JSONResponse

    Raises:
        HTTPException: For any unexpected errors during processing
    """
    try:
        payload, headers = verified_data

        # Process webhook event via service
        result = await process_webhook_event(
            payload=payload,
            headers=headers,
        )

        return JSONResponse(status_code=status.HTTP_200_OK, content=result)

    except Exception as e:
        logger.error(
            f"Error handling webhook for event {payload.event_id}: {type(e).__name__}: {str(e)}",
            exc_info=True,
        )
        # Return 200 OK even on error to avoid Linq retrying (errors are logged internally)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ok",
                "note": "Event processed with errors - check logs",
                "event_id": payload.event_id,
            },
        )
