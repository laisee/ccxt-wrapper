import signal
from contextlib import contextmanager

import pytest


@contextmanager
def time_limit(seconds: int):
    def handler(signum, frame):
        raise TimeoutError(f"Timed out after {seconds} seconds")

    previous_handler = signal.signal(signal.SIGALRM, handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)


def skip_if_missing_env_vars(required_vars: dict[str, str | None]) -> None:
    missing = [name for name, value in required_vars.items() if not value]
    if missing:
        pytest.skip(f"Missing live exchange credentials: {', '.join(missing)}")


def require_live_auth(exchange, required_vars: dict[str, str | None]):
    skip_if_missing_env_vars(required_vars)
    try:
        with time_limit(2):
            balance = exchange.fetch_balance()
    except TimeoutError:
        pytest.skip(f"Skipping live {exchange.exchange_name} tests: auth check timed out.")

    if balance is None:
        pytest.skip(
            f"Skipping live {exchange.exchange_name} tests: credentials are invalid, expired, or missing required permissions."
        )
    return exchange