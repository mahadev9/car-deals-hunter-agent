"""Analytics logging module with database storage."""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from database.core import get_session
from database.models.webhook_event_analytics import WebhookEventAnalytics


class DatabaseLoggingHandler(logging.Handler):
    """Custom logging handler that stores analytics events in database."""

    def emit(self, record: logging.LogRecord) -> None:
        """Store log record to database."""
        try:
            # Only process records with analytics data
            if "analytics" not in record.msg:
                return

            analytics_data = record.msg["analytics"]
            session = get_session()

            try:
                # Extract metadata
                metadata = analytics_data.get("metadata", {})
                metadata_json = metadata if metadata else None

                # Create analytics record
                event = WebhookEventAnalytics(
                    event_id=analytics_data.get("event_id"),
                    event_type=analytics_data.get("event_type"),
                    status=analytics_data.get("status", "processed"),
                    sender_handle=metadata.get("sender"),
                    chat_id=metadata.get("chat_id"),
                    message_id=metadata.get("message_id"),
                    error_message=analytics_data.get("error"),
                    metadata_json=metadata_json,
                    processing_duration_ms=metadata.get("duration_ms"),
                )

                session.add(event)
                session.commit()

            except Exception:
                session.rollback()
                self.handleError(record)

            finally:
                session.close()

        except Exception:
            self.handleError(record)


def configure_analytics_logging() -> None:
    """Configure analytics logging with database handlers."""

    analytics_logger = logging.getLogger("analytics")
    analytics_logger.setLevel(logging.INFO)

    # Database handler for analytics storage
    db_handler = DatabaseLoggingHandler()

    # Remove any existing handlers
    analytics_logger.handlers.clear()

    # Add db handlers
    analytics_logger.addHandler(db_handler)
    analytics_logger.propagate = False


def log_event_analytics(
    event_type: str,
    event_id: str,
    metadata: Dict[str, Any],
    status: str = "processed",
    error: Optional[str] = None,
) -> None:
    """
    Log event analytics with structured data.

    Args:
        event_type: Type of webhook event
        event_id: Unique event identifier
        metadata: Event metadata (sender, recipient, message details, etc.)
        status: Processing status (processed, failed, duplicated, etc.)
        error: Error message if processing failed
    """
    analytics_logger = logging.getLogger("analytics")

    analytics_data = {
        "event_type": event_type,
        "event_id": event_id,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata,
    }

    if error:
        analytics_data["error"] = error

    analytics_logger.info({"analytics": analytics_data})
