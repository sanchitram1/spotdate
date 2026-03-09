import logging


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Return a configured logger with a simple console handler.

    - `name`: usually `__name__` from the caller.
    - `level`: int (e.g. logging.DEBUG) or string (e.g. "DEBUG").
    """
    logger = logging.getLogger(name)

    if isinstance(level, str):
        level = level.upper()
        numeric_level = logging.getLevelName(level)
        if not isinstance(numeric_level, int):
            raise ValueError(f"Invalid log level: {level}")
        logger.setLevel(numeric_level)
    else:
        logger.setLevel(level)

    # Only add handler once per logger
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.propagate = False
    return logger
