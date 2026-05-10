from datetime import datetime

from sqlalchemy import Column, DateTime, String

from database.core import Base


class WebhookEvent(Base):
    """Model for tracking processed webhook events."""

    __tablename__ = "webhook_events"

    event_id = Column(String, primary_key=True, index=True)
    event_type = Column(String, nullable=False)
    processed_at = Column(DateTime, default=datetime.now, nullable=False)

    def __repr__(self) -> str:
        return f"<WebhookEvent(event_id={self.event_id}, event_type={self.event_type}, processed_at={self.processed_at})>"
