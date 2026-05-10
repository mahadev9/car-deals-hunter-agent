import logging
from datetime import datetime, timedelta

from sqlalchemy import and_, update

from database.core import get_session
from database.models.pending_message_processing import PendingMessageProcessing

logger = logging.getLogger(__name__)


def schedule_message_processing(
    *,
    chat_id: str,
    sender: str,
    message_id: str | None,
    user_message: str,
    event_id: str,
    delay_seconds: int,
) -> tuple[datetime, int]:
    """Create or refresh the pending processing job for a chat."""

    session = get_session()

    try:
        now = datetime.now()
        process_at = now + timedelta(seconds=delay_seconds)

        pending_job = session.get(PendingMessageProcessing, chat_id)
        if pending_job is None:
            pending_job = PendingMessageProcessing(
                chat_id=chat_id,
                event_id=event_id,
                sender=sender,
                message_id=message_id,
                user_message=user_message,
                generation=1,
                status="pending",
                process_at=process_at,
                completed_at=None,
                processing_started_at=None,
            )
            session.add(pending_job)
        else:
            pending_job.event_id = event_id
            pending_job.sender = sender
            pending_job.message_id = message_id
            pending_job.user_message = user_message
            pending_job.generation += 1
            pending_job.status = "pending"
            pending_job.process_at = process_at
            pending_job.completed_at = None
            pending_job.processing_started_at = None

        session.commit()
        return process_at, pending_job.generation

    except Exception as e:
        session.rollback()
        logger.error(f"Database error scheduling message processing: {str(e)}")
        raise

    finally:
        session.close()


def list_due_pending_jobs(now: datetime) -> list[PendingMessageProcessing]:
    """Return jobs whose quiet window has expired."""

    session = get_session()

    try:
        return (
            session.query(PendingMessageProcessing)
            .filter(
                PendingMessageProcessing.status == "pending",
                PendingMessageProcessing.completed_at.is_(None),
                PendingMessageProcessing.process_at <= now,
            )
            .order_by(PendingMessageProcessing.process_at.asc())
            .all()
        )
    finally:
        session.close()


def claim_pending_job(
    chat_id: str,
    generation: int,
) -> bool:
    """Atomically claim a pending job for processing."""

    session = get_session()

    try:
        now = datetime.now()
        result = session.execute(
            update(PendingMessageProcessing)
            .where(
                and_(
                    PendingMessageProcessing.chat_id == chat_id,
                    PendingMessageProcessing.generation == generation,
                    PendingMessageProcessing.status == "pending",
                    PendingMessageProcessing.completed_at.is_(None),
                    PendingMessageProcessing.process_at <= now,
                )
            )
            .values(
                status="processing",
                processing_started_at=now,
            )
        )
        session.commit()

        if result.rowcount != 1:
            return False

        return True

    except Exception as e:
        session.rollback()
        logger.error(f"Database error claiming pending message job: {str(e)}")
        raise

    finally:
        session.close()


def get_pending_job(chat_id: str) -> PendingMessageProcessing | None:
    """Fetch the current pending job for a chat."""

    session = get_session()

    try:
        return (
            session.query(PendingMessageProcessing)
            .filter(
                PendingMessageProcessing.chat_id == chat_id,
                PendingMessageProcessing.completed_at.is_(None),
            )
            .one_or_none()
        )
    finally:
        session.close()


def complete_pending_job(
    chat_id: str,
    generation: int,
) -> bool:
    """Mark a job as completed so it cannot be processed again."""

    session = get_session()

    try:
        now = datetime.now()
        result = session.execute(
            update(PendingMessageProcessing)
            .where(
                and_(
                    PendingMessageProcessing.chat_id == chat_id,
                    PendingMessageProcessing.generation == generation,
                    PendingMessageProcessing.status == "processing",
                    PendingMessageProcessing.completed_at.is_(None),
                )
            )
            .values(
                status="done",
                completed_at=now,
                processing_started_at=None,
            )
        )
        session.commit()
        return result.rowcount == 1

    except Exception as e:
        session.rollback()
        logger.error(f"Database error completing pending message job: {str(e)}")
        raise

    finally:
        session.close()
