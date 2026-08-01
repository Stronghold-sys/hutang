import logging
import sys
from app.core.config import settings


def setup_logging():
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_level = logging.DEBUG if settings.APP_DEBUG else logging.INFO

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger(settings.APP_NAME)
    logger.setLevel(log_level)
    return logger


logger = setup_logging()
