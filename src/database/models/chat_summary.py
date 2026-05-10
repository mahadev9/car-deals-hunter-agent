from datetime import datetime

from sqlalchemy import Column, DateTime, String

from database.core import Base


class ChatSummary(Base):
    """Model for storing chat summaries."""

    __tablename__ = "chat_summaries"

    chat_id = Column(String, primary_key=True, index=True)
    summary = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )
