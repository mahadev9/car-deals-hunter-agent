"""Database model for detailed webhook event analytics."""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Index, Integer, String, Text

from database.core import Base


class WebhookEventAnalytics(Base):
    """Model for storing detailed webhook event analytics data."""

    __tablename__ = "webhook_event_analytics"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Event identifiers
    event_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)

    # Status tracking
    status = Column(
        String, default="processed", nullable=False
    )  # processed, failed, duplicated
    processing_timestamp = Column(
        DateTime, default=datetime.now, nullable=False, index=True
    )

    # Sender/Recipient info
    sender_handle = Column(String, nullable=True, index=True)
    recipient_handle = Column(String, nullable=True)
    chat_id = Column(String, nullable=True, index=True)
    is_group_chat = Column(Integer, default=0, nullable=False)

    # Message/Content data
    message_id = Column(String, nullable=True)
    message_content_length = Column(Integer, nullable=True)
    service_type = Column(String, nullable=True)  # iMessage, SMS, RCS

    # Reaction/Interaction data
    reaction_type = Column(String, nullable=True)
    participant_handle = Column(String, nullable=True)

    # Error handling
    error_code = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)

    # Metadata
    metadata_json = Column(JSON, nullable=True)  # JSON object of additional data
    processing_duration_ms = Column(Integer, nullable=True)

    # Indexes for common queries
    __table_args__ = (
        Index("idx_event_type_timestamp", "event_type", "processing_timestamp"),
        Index("idx_sender_timestamp", "sender_handle", "processing_timestamp"),
        Index("idx_status_timestamp", "status", "processing_timestamp"),
    )

    def __repr__(self) -> str:
        return (
            f"<WebhookEventAnalytics("
            f"event_id={self.event_id}, "
            f"event_type={self.event_type}, "
            f"status={self.status}, "
            f"sender={self.sender_handle})>"
        )
