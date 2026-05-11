from pathlib import Path

from loguru import logger


def log_reading_file(path: str | Path, extra: str = "") -> None:
    logger.info(f"<= {path}{extra}")


def log_writing_file(path: str | Path | Path, extra: str = "") -> None:
    logger.info(f"=> {path}{extra}")
