import logging
import logging.handlers
import sys
import os
import io
from config import config as Config

def setup_logging(level="INFO", log_file=None, max_bytes=10*1024*1024, backup_count=5):
    """Setup production-ready logging with rotation."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Fix Windows console encoding for Unicode support
    if os.name == 'nt':  # Windows
        try:
            # Set console to UTF-8 encoding
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleOutputCP(65001)  # UTF-8 codepage
            kernel32.SetConsoleCP(65001)  # UTF-8 input codepage
        except:
            pass  # Ignore if setting encoding fails

    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file) if log_file else "logs"
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # Default log file
    if not log_file:
        log_file = os.path.join(log_dir, "bot.log")

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        '%(levelname)s | %(message)s'
    )

    # Setup handlers
    handlers = []

    # Console handler with UTF-8 encoding
    try:
        # Try to create a UTF-8 encoded stream handler
        console_handler = logging.StreamHandler(io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8'))
    except:
        # Fallback to regular handler if UTF-8 wrapper fails
        console_handler = logging.StreamHandler(sys.stdout)

    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_formatter)
    handlers.append(console_handler)

    # File handler with rotation
    if Config.is_production:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
    else:
        # Use simple file handler for development
        file_handler = logging.FileHandler(log_file)

    file_handler.setLevel(log_level)
    file_handler.setFormatter(detailed_formatter)
    handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        force=True  # Override any existing configuration
    )

    # Set specific log levels for noisy libraries
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("discord.http").setLevel(logging.WARNING)
    logging.getLogger("discord.gateway").setLevel(logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    # Log startup information
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized at level {level}")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Environment: {'production' if Config.is_production else 'development'}")