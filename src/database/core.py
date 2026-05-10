import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from config import settings

logger = logging.getLogger(__name__)

# Database URL for SQLite
DATABASE_URL = f"sqlite:///{settings.APP_DATABASE_PATH}"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


def init_database() -> None:
    """Initialize database schema."""

    os.makedirs(os.path.join(settings.MOUNT_FOLDER, "db"), exist_ok=True)

    Base.metadata.create_all(bind=engine)
    logger.info(f"Database initialized at {settings.APP_DATABASE_PATH}")


def get_session() -> Session:
    """Get a database session."""
    return Session(engine)
