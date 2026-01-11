"""
Shared utilities for NovelVerified.AI agents.

Provides:
- Centralized logging configuration
- Common retry decorators
- Validation helpers
"""

import logging
import functools
import time
import random
from pathlib import Path


def setup_logger(name: str, log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with console and optional file output.
    
    Args:
        name: Logger name (usually __name__ of the calling module)
        log_file: Optional log file path. If None, logs to console only.
        level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(level)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    
    return logger


def retry_with_backoff(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,),
    logger: logging.Logger = None
):
    """
    Decorator for retrying a function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exceptions: Tuple of exceptions to catch and retry
        logger: Optional logger for retry messages
    
    Returns:
        Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries - 1:
                        if logger:
                            logger.error(f"{func.__name__} failed after {max_retries} attempts: {e}")
                        raise
                    
                    # Calculate delay with jitter
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    jitter = delay * 0.25 * (2 * random.random() - 1)
                    total_delay = delay + jitter
                    
                    if logger:
                        logger.warning(
                            f"{func.__name__} attempt {attempt + 1}/{max_retries} failed: {e}. "
                            f"Retrying in {total_delay:.1f}s"
                        )
                    
                    time.sleep(total_delay)
            
            raise last_exception
        
        return wrapper
    return decorator


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


def validate_claim_data(claim_data: dict) -> bool:
    """
    Validate claim data structure.
    
    Args:
        claim_data: Dictionary containing claim information
    
    Returns:
        True if valid
    
    Raises:
        ValidationError: If required fields are missing
    """
    required_fields = ["claim_id", "book_name", "character", "claim_text"]
    
    for field in required_fields:
        if field not in claim_data:
            raise ValidationError(f"Missing required field: {field}")
        if not claim_data[field]:
            raise ValidationError(f"Empty required field: {field}")
    
    return True


def validate_evidence_data(evidence_data: dict) -> bool:
    """
    Validate evidence data structure.
    
    Args:
        evidence_data: Dictionary containing evidence information
    
    Returns:
        True if valid
    
    Raises:
        ValidationError: If required fields are missing
    """
    required_fields = ["claim_id", "book_name", "character", "claim_text", "evidence"]
    
    for field in required_fields:
        if field not in evidence_data:
            raise ValidationError(f"Missing required field: {field}")
    
    if not isinstance(evidence_data["evidence"], list):
        raise ValidationError("Evidence must be a list")
    
    if len(evidence_data["evidence"]) == 0:
        raise ValidationError("Evidence list cannot be empty")
    
    # Validate each evidence item
    evidence_fields = ["chunk_idx", "book", "text", "score"]
    for i, ev in enumerate(evidence_data["evidence"]):
        for field in evidence_fields:
            if field not in ev:
                raise ValidationError(f"Evidence item {i} missing field: {field}")
    
    return True
