import logging
from pathlib import Path


def setup_logger():
    """Set up the logger."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    error_log = Path("logs/errors.log")
    error_log.parent.mkdir(exist_ok=True)
    fh = logging.FileHandler(error_log, encoding="utf-8")
    fh.setLevel(logging.ERROR)
    fh.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logging.getLogger().addHandler(fh)


logger = logging.getLogger(__name__)
setup_logger()
