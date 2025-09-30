"""Logging configuration for dropfix"""
import logging
import sys

# Configure root logger
logger = logging.getLogger("dropfix")
logger.setLevel(logging.WARNING)  # Default to WARNING

# Console handler
_console_handler = logging.StreamHandler(sys.stderr)
_console_handler.setLevel(logging.DEBUG)
_formatter = logging.Formatter("%(levelname)s: %(message)s")
_console_handler.setFormatter(_formatter)
logger.addHandler(_console_handler)

# Prevent propagation to root logger
logger.propagate = False


def set_verbosity(verbose: int = 0):
    """Set logging verbosity level

    Args:
        verbose: Verbosity level (0=WARNING, 1=INFO, 2+=DEBUG)
    """
    if verbose == 0:
        logger.setLevel(logging.WARNING)
    elif verbose == 1:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.DEBUG)