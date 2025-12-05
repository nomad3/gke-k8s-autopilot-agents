"""Logging configuration using loguru"""

import sys
from loguru import logger

from ..core.config import settings

# Remove default handler
logger.remove()

# Add custom handler based on environment
if settings.log_format == "json":
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level=settings.log_level,
        serialize=True,
    )
else:
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
        level=settings.log_level,
        colorize=True,
    )

# Export logger
__all__ = ["logger"]
