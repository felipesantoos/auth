"""
Logging Configuration
Structured logging with JSON support for production
"""
import logging
import sys
from typing import Any
from pythonjsonlogger import jsonlogger
import os


def setup_logging(level: str = "INFO") -> None:
    """
    Configure structured logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Use JSON formatter for production, simple formatter for development
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "production":
        # JSON formatter for production (easier to parse by log aggregators)
        json_formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d',
            rename_fields={
                "asctime": "timestamp",
                "levelname": "level",
                "pathname": "file",
                "lineno": "line"
            }
        )
        console_handler.setFormatter(json_formatter)
    else:
        # Simple formatter for development
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("aiokafka").setLevel(logging.WARNING)

