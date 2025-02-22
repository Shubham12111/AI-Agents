import logging
import sys
import json
import traceback
from datetime import datetime
from enum import Enum, unique
from rich.logging import RichHandler

@unique
class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

class LoggerUtils:
    def __init__(self, name: str, log_level: LogLevel = LogLevel.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level.value)

        # Use RichHandler for better console logs
        rich_handler = RichHandler()
        self.logger.addHandler(rich_handler)

    def log(self, level: LogLevel, msg: str, error: Exception = None, **kwargs):
        """Log messages with optional error details."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level.name,
            "message": msg,
            "details": kwargs,
        }

        if error:
            log_entry["error"] = {
                "message": str(error),
                "traceback": traceback.format_exc()
            }

        self.logger.log(level.value, json.dumps(log_entry, indent=2))

    def debug(self, msg, **kwargs): self.log(LogLevel.DEBUG, msg, **kwargs)
    def info(self, msg, **kwargs): self.log(LogLevel.INFO, msg, **kwargs)
    def warning(self, msg, **kwargs): self.log(LogLevel.WARNING, msg, **kwargs)
    def error(self, msg, error=None, **kwargs): self.log(LogLevel.ERROR, msg, error, **kwargs)
    def critical(self, msg, error=None, **kwargs): self.log(LogLevel.CRITICAL, msg, error, **kwargs)

if __name__ == "__main__":
    logger = LoggerUtils("app_logger", LogLevel.DEBUG)

    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message", error=ValueError("Example error"))
    logger.critical("This is a critical error", error=RuntimeError("Critical failure"))
