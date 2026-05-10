import logging
from typing import Optional

from database.core import get_session
from database.models.chat_summary import ChatSummary

logger = logging.getLogger(__name__)


async def get_summary_for_chat(chat_id: str) -> Optional[str]:
    """Fetch the summary for a given chat, if it exists."""

    session = get_session()

    try:
        summary_record = (
            session.query(ChatSummary)
            .filter(ChatSummary.chat_id == chat_id)
            .one_or_none()
        )

        if summary_record:
            return summary_record.summary

        return None
    except Exception as e:
        session.rollback()
        logger.error(
            f"Database error fetching chat summary for chat_id {chat_id}: {str(e)}"
        )
        raise
    finally:
        session.close()


async def upsert_summary_for_chat(chat_id: str, summary: str) -> None:
    """Insert or update the summary for a given chat."""

    session = get_session()

    try:
        summary_record = (
            session.query(ChatSummary)
            .filter(ChatSummary.chat_id == chat_id)
            .one_or_none()
        )

        if summary_record is None:
            summary_record = ChatSummary(chat_id=chat_id, summary=summary)
            session.add(summary_record)
        else:
            summary_record.summary = summary

        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(
            f"Database error upserting chat summary for chat_id {chat_id}: {str(e)}"
        )
        raise
    finally:
        session.close()
