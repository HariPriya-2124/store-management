"""
Logging utility for Store Management System.
Configures structured file and console logging with automatic rotation.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import LOG_FILE

_logger = None

def get_logger(name: str = "StoreManagementSystem") -> logging.Logger:
    """
    Returns a configured singleton logger with rotating file and console handlers.
    """
    global _logger
    if _logger is not None:
        return _logger.getChild(name) if name != "StoreManagementSystem" else _logger

    logger = logging.getLogger("StoreManagementSystem")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Prevent duplicate handlers if re-initialized
    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Rotating File Handler (Max 5MB per file, up to 3 backups)
        try:
            LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
            )
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not configure file logging: {e}", file=sys.stderr)

        # Standard Stream / Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    _logger = logger
    return _logger.getChild(name) if name != "StoreManagementSystem" else _logger

