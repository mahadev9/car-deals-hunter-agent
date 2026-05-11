import logging
from datetime import datetime, timedelta

from sqlalchemy import select

from config import settings
from database.core import get_session
from database.models.webhook_event import WebhookEvent

logger = logging.getLogger("car-deals-hunter")


def is_duplicate_event(event_id: str, event_type: str) -> bool:
    """Check if event has already been processed.

    Args:
        event_id: Unique event identifier
        event_type: Type of the event

    Returns:
        True if event was already processed, False otherwise
    """
    session = get_session()

    try:
        # Check if event already exists
        stmt = select(WebhookEvent).where(WebhookEvent.event_id == event_id)
        existing_event = session.execute(stmt).scalar_one_or_none()

        if existing_event:
            return True

        # Mark event as processed
        new_event = WebhookEvent(
            event_id=event_id, event_type=event_type, processed_at=datetime.now()
        )
        session.add(new_event)

        # Clean up old events
        cutoff = datetime.now() - timedelta(hours=settings.EVENT_EXPIRATION_HOURS)
        stmt = select(WebhookEvent).where(WebhookEvent.processed_at < cutoff)
        old_events = session.execute(stmt).scalars().all()
        for old_event in old_events:
            session.delete(old_event)

        session.commit()
        return False

    except Exception as e:
        session.rollback()
        logger.error(f"Database error checking duplicate event: {str(e)}")
        raise

    finally:
        session.close()


def get_processed_events_count() -> int:
    """Get total count of processed events.

    Returns:
        Number of webhook events in database
    """
    session = get_session()

    try:
        stmt = select(WebhookEvent)
        count = len(session.execute(stmt).scalars().all())
        return count

    finally:
        session.close()


def clear_old_events(expiration_hours: int = 24) -> int:
    """Clear events older than expiration_hours.

    Args:
        expiration_hours: Hours after which to consider events expired

    Returns:
        Number of events deleted
    """
    session = get_session()

    try:
        cutoff = datetime.now() - timedelta(hours=expiration_hours)
        stmt = select(WebhookEvent).where(WebhookEvent.processed_at < cutoff)
        old_events = session.execute(stmt).scalars().all()

        deleted_count = len(old_events)
        for old_event in old_events:
            session.delete(old_event)

        session.commit()
        logger.info(f"Deleted {deleted_count} old webhook events")
        return deleted_count

    except Exception as e:
        session.rollback()
        logger.error(f"Database error clearing old events: {str(e)}")
        raise

    finally:
        session.close()
