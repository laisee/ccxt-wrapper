import os
import sys

import pytest
from dotenv import load_dotenv

load_dotenv(".env")
# Add the parent folder to the system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from clients.exchange_utils import format_pair
from clients.gateio import Gate

NAME = "gate"
API_KEY = os.getenv("GATEIO_PROD_APIKEY")
API_SECRET = os.getenv("GATEIO_PROD_SECRET")
CCXT_CONFIG = {}


@pytest.fixture
def gate():
    return Gate(API_KEY, API_SECRET, CCXT_CONFIG)


class TestGate:
    @pytest.mark.base
    @pytest.mark.github
    def test_gate_exists(self, gate):
        assert gate is not None

    @pytest.mark.base
    @pytest.mark.github
    def test_env_vars(self):
        assert API_KEY is not None
        assert API_SECRET is not None

    @pytest.mark.base
    @pytest.mark.github
    def test_gate_name(self, gate):
        assert gate.exchange_name is not None
        assert gate.exchange_name == NAME

    @pytest.mark.base
    def test_gate_balance_not_None(self, gate):
        balances = gate.fetch_balance()
        assert balances is not None

    @pytest.mark.base
    @pytest.mark.parametrize("symbol", ["ETH", "BTC", "DOT", "SOL", "XRP"])
    def test_gate_ticker(self, gate: gate, symbol: str):
        pair = format_pair(symbol, gate.quote_currency, gate.divider)
        ticker = gate.fetch_ticker(pair)
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
    def test_gate_format_pair(self, gate: gate, symbol: str, expected_pair: str):
        pair = format_pair(symbol, gate.quote_currency, gate.divider)
        assert pair == expected_pair
