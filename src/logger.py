import logging
import logging.config
from pathlib import Path


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s | %(name)s | %(module)s | %(funcName)s | %(levelname)s | %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": logging.INFO,
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "standard",
            "level": logging.INFO,
            "filename": "logs/app.log",
            "mode": "a",
            "maxBytes": 10485760,
            "backupCount": 5,
            "encoding": "utf8",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": logging.INFO,
    },
}


def bootstrap_logging() -> None:
    logs_path = Path("logs")
    logs_path.mkdir(parents=True, exist_ok=True)

    logging.config.dictConfig(LOGGING_CONFIG)
