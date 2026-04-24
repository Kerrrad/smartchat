import logging
from logging.config import dictConfig

from app.core.config import settings


def setup_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "level": settings.log_level,
                }
            },
            "root": {"handlers": ["console"], "level": settings.log_level},
        }
    )


logger = logging.getLogger("smartchat")

