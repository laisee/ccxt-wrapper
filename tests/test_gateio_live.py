import os
import sys

import pytest
from dotenv import load_dotenv

load_dotenv(".env")
# Add the parent folder to the system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from conftest import require_live_auth, skip_if_missing_env_vars
from clients.exchange_utils import format_pair
from clients.gateio import Gate

NAME = "gate"
API_KEY = os.getenv("GATEIO_PROD_APIKEY")
API_SECRET = os.getenv("GATEIO_PROD_SECRET")
REQUIRED_ENV_VARS = {
    "GATEIO_PROD_APIKEY": API_KEY,
    "GATEIO_PROD_SECRET": API_SECRET,
}
CCXT_CONFIG = {}


@pytest.fixture
def gate():
    return Gate(API_KEY, API_SECRET, CCXT_CONFIG)


@pytest.fixture(scope="module")
def authenticated_gate():
    exchange = Gate(API_KEY, API_SECRET, CCXT_CONFIG)
    return require_live_auth(exchange, REQUIRED_ENV_VARS)


class TestGate:
    @pytest.mark.base
    @pytest.mark.github
    def test_gate_exists(self, gate):
        assert gate is not None

    @pytest.mark.base
    @pytest.mark.github
    def test_env_vars(self):
        skip_if_missing_env_vars(REQUIRED_ENV_VARS)
        assert API_KEY is not None
        assert API_SECRET is not None

    @pytest.mark.base
    @pytest.mark.github
    def test_gate_name(self, gate):
        assert gate.exchange_name is not None
        assert gate.exchange_name == NAME

    @pytest.mark.base
    def test_gate_balance_not_None(self, authenticated_gate):
        balances = authenticated_gate.fetch_balance()
        assert balances is not None

    @pytest.mark.base
    @pytest.mark.parametrize("symbol", ["ETH", "BTC", "DOT", "SOL", "XRP"])
    def test_gate_ticker(self, authenticated_gate: Gate, symbol: str):
        pair = format_pair(symbol, authenticated_gate.quote_currency, authenticated_gate.divider)
        ticker = authenticated_gate.fetch_ticker(pair)
        assert ticker is not None, f"Ticker {ticker}"
        assert float(ticker["ask"]) > 0.00
        assert float(ticker["bid"]) > 0.00
        assert float(ticker["high"]) > 0.00
        assert float(ticker["low"]) > 0.0

    @pytest.mark.base
    @pytest.mark.parametrize(
        "symbol,expected_pair",
        [
            ("ETH", "ETH/USDT"),
            ("XRP", "XRP/USDT"),
        ],
    )
    @pytest.mark.github
    def test_gate_format_pair(self, gate: Gate, symbol: str, expected_pair: str):
        pair = format_pair(symbol, gate.quote_currency, gate.divider)
        assert pair == expected_pair
