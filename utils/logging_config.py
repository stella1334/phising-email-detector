import sys
from loguru import logger
from config import settings

def setup_logging():
    """Configure logging for the application"""
    
    # Remove default handler
    logger.remove()
    
    # Add console handler with custom format
    logger.add(
        sys.stdout,
        format=settings.log_format,
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # Add file handler for production
    if not settings.debug:
        logger.add(
            "logs/phishing_detector.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=settings.log_level,
            rotation="10 MB",
            retention="30 days",
            compression="zip"
        )
    
    return logger
