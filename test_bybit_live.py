import os
import sys

import pytest
from dotenv import load_dotenv

load_dotenv(".env")
# Add the parent folder to the system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from clients.exchange_utils import format_pair
from clients.bybit import Bybit

NAME = "bybit"
API_KEY = os.getenv("BYBIT_PROD_APIKEY")
API_SECRET = os.getenv("BYBIT_PROD_SECRET")
CCXT_CONFIG = {"set_sandbox_mode": False}

@pytest.fixture
def bybit():
    return Bybit(API_KEY, API_SECRET, CCXT_CONFIG)


class Testbybit:
    @pytest.mark.github
    @pytest.mark.base
    def test_bybit_exists(self, bybit):
        assert bybit is not None

    @pytest.mark.github
    @pytest.mark.base
    def test_env_vars(self):
        assert API_KEY is not None
        assert API_SECRET is not None

    @pytest.mark.github
    @pytest.mark.base
    def test_bybit_name(self, bybit):
        assert bybit.exchange_name is not None
        assert bybit.exchange_name == NAME

    @pytest.mark.base
    def test_bybit_balance_not_None(self, bybit):
        balances = bybit.fetch_balance()
        assert balances is not None

    @pytest.mark.base
    @pytest.mark.parametrize("symbol", ["ETH", "BTC", "DOT", "SOL", "XRP"])
    def test_bybit_ticker(self, bybit: Bybit, symbol: str):
        pair = format_pair(symbol, bybit.quote_currency, bybit.divider)
        ticker = bybit.fetch_ticker(pair)
        assert ticker is not None, f"Ticker {ticker}"
        assert float(ticker["ask"]) > 0.00
        assert float(ticker["bid"]) > 0.00
        assert float(ticker["high"]) > 0.00
        assert float(ticker["low"]) > 0.0

    @pytest.mark.parametrize(
        "symbol,expected_pair",
        [
            ("ETH", "ETH/USDT"),
            ("XRP", "XRP/USDT"),
        ],
    )
    @pytest.mark.base
    @pytest.mark.github
    @pytest.mark.base
    def test_bybit_format_pair(self, bybit: Bybit, symbol: str, expected_pair: str):
        pair = format_pair(symbol, bybit.quote_currency, bybit.divider)
        assert pair == expected_pair
