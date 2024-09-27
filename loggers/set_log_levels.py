import logging


def set_loggers(verbosity: int = 0, api_verbosity: str = "info") -> None:
    """
    Set the logging level for third party libraries
    :param verbosity: Verbosity level
    :param api_verbosity: Verbosity level for API logs
    :return: None
    """
    for logger_name in ("requests", "urllib3", "httpcore"):
        logging.getLogger(logger_name).setLevel(
            logging.INFO if verbosity <= 1 else logging.DEBUG
        )
    logging.getLogger("ccxt.base.exchange").setLevel(
        logging.INFO if verbosity <= 2 else logging.DEBUG
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logging.getLogger("werkzeug").setLevel(
        logging.ERROR if api_verbosity == "error" else logging.INFO
    )
