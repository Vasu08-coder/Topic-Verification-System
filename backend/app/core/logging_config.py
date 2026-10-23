import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import settings


def setup_logging() -> logging.Logger:
    environment = settings.ENVIRONMENT.lower()
    level_map = {
        "dev": logging.DEBUG,
        "staging": logging.INFO,
        "prod": logging.WARNING,
    }

    level = level_map.get(environment, logging.INFO)

    logger = logging.getLogger("topic_verifier")
    logger.setLevel(level)

    if logger.handlers:
        logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    file_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.propagate = False

    return logger


logger = setup_logging()
