import logging
import logging.handlers
import sys
from pathlib import Path

# Constants
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

def setup_logging(log_dir: Path, debug_mode: bool = False):
    """
    Configure the root logger with rotating file handler and console handler.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "docnexus.log"
    
    root_logger = logging.getLogger()
    
    # Set base level
    root_logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    
    # 1. Rotating File Handler
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=LOG_FILE_SIZE,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG) # Always capture detailed logs to file
    
    # 2. Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)
    
    # Clean up existing handlers to avoid duplicates on reload/restart logic check
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    logging.info(f"Logging initialized. Log file: {log_file}")
    
    # Quiet down some noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.WARNING) # Flask dev server noise
