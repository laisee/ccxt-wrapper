import logging
from logging import FileHandler, Formatter, StreamHandler

from loggers.set_log_levels import set_loggers

LOGFORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def setup_logging(
    verbosity: int = 1, logfile: str = "app.log", api_verbosity: str = "info"
) -> None:
    """
    Setup logging configuration.
    :param verbosity: Verbosity level (0 for INFO, 1 for DEBUG)
    :param logfile: Optional log file path
    :param api_verbosity: Verbosity level for API logs
    """
    log_level = logging.DEBUG if verbosity > 0 else logging.INFO

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Create console handler
    console_handler = StreamHandler()
    console_handler.setFormatter(Formatter(LOGFORMAT))
    logger.addHandler(console_handler)

    # Create file handler if logfile is specified
    if logfile:
        file_handler = FileHandler(logfile)
        file_handler.setFormatter(Formatter(LOGFORMAT))
        logger.addHandler(file_handler)

    logger.info(
        "Logging setup complete. Verbosity set to %s",
        "DEBUG" if verbosity > 0 else "INFO",
    )

    # Set log levels for third-party libraries
    set_loggers(verbosity, api_verbosity)
