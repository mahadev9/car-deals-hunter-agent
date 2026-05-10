from datetime import datetime
from typing import Any, Dict

from linq.types import WebhookEventType
from pydantic import BaseModel, Field, field_validator


class WebhookEvent(BaseModel):
    api_version: str = Field(..., description="API version of the webhook event")
    webhook_version: str = Field(
        ..., description="Version of the webhook payload format"
    )
    event_type: WebhookEventType = Field(..., description="Type of the webhook event")
    event_id: str = Field(..., description="Unique identifier for the webhook event")
    created_at: datetime = Field(
        ..., description="Timestamp of when the event occurred"
    )
    trace_id: str = Field(..., description="Trace identifier for the webhook request")
    partner_id: str = Field(
        ..., description="Partner identifier associated with the event"
    )
    data: Dict[str, Any] = Field(..., description="Payload of the webhook event")

    @field_validator("api_version")
    def validate_api_version(cls, value: str) -> str:
        if value != "v3":
            raise ValueError("api_version must be 'v3'")
        return value

    @field_validator("webhook_version")
    def validate_webhook_version(cls, value: str) -> str:
        if value != "2026-02-03":
            raise ValueError("webhook_version must be '2026-02-03'")
        return value


class WebhookEventHeaders(BaseModel):
    timestamp: str = Field(..., description="Timestamp from the webhook header")
    event_type: WebhookEventType = Field(
        ..., description="Event type from the webhook header"
    )
    subscription_id: str = Field(
        ..., description="Subscription ID from the webhook header"
    )
