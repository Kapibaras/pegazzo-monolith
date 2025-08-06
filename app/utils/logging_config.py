import logging
from pathlib import Path


def setup_logger():
    """Set up the logger."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


logger = logging.getLogger(__name__)
setup_logger()
