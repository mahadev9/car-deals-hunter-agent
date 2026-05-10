from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from database.core import Base


class PendingMessageProcessing(Base):
    """Model for coalesced message processing jobs."""

    __tablename__ = "pending_message_processing"

    chat_id = Column(String, primary_key=True, index=True)
    event_id = Column(String, nullable=False, index=True)
    sender = Column(String, nullable=False)
    message_id = Column(String, nullable=True)
    user_message = Column(Text, nullable=False)
    generation = Column(Integer, nullable=False, default=1)
    status = Column(String, nullable=False, default="pending", index=True)
    process_at = Column(DateTime, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True, index=True)
    processing_started_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

    def __repr__(self) -> str:
        return (
            "<PendingMessageProcessing("
            f"chat_id={self.chat_id}, generation={self.generation}, process_at={self.process_at})>"
        )
