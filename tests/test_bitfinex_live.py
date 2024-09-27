import os
import sys

import pytest
from dotenv import load_dotenv

load_dotenv(".env")
# Add the parent folder to the system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from clients.exchange_utils import format_pair
from clients.bitfinex import Bitfinex

NAME = "bitfinex"
API_KEY = os.getenv("BITFINEX_PROD_APIKEY")
API_SECRET = os.getenv("BITFINEX_PROD_SECRET")


@pytest.fixture
def bitfinex():
    return Bitfinex(API_KEY, API_SECRET)


class TestBitfinex:
    @pytest.mark.base
    @pytest.mark.github
    def test_bitfinex_exists(self, bitfinex):
        assert bitfinex is not None

    @pytest.mark.base
    @pytest.mark.github
    def test_env_vars(self):
        assert API_KEY is not None
        assert API_SECRET is not None

    @pytest.mark.base
    @pytest.mark.github
    def test_bitfinex_name(self, bitfinex):
        assert bitfinex.exchange_name is not None
        assert bitfinex.exchange_name == NAME

    @pytest.mark.base
    @pytest.mark.github
    def test_bitfinex_balance_not_None(self, bitfinex):
        balances = bitfinex.fetch_balance()
        assert balances is not None

    @pytest.mark.base
    @pytest.mark.github
    @pytest.mark.parametrize("symbol", ["ETH", "BTC", "DOT", "SOL", "XRP"])
    def test_bitfinex_ticker(self, bitfinex: Bitfinex, symbol: str):
        pair = format_pair(symbol, bitfinex.quote_currency, bitfinex.divider)
        ticker = bitfinex.fetch_ticker(pair)
        assert ticker is not None, f"Ticker {ticker}"
        assert float(ticker["ask"]) > 0.00
        assert float(ticker["bid"]) > 0.00
        assert float(ticker["high"]) > 0.00
        assert float(ticker["low"]) > 0.0

    @pytest.mark.base
    @pytest.mark.github
    @pytest.mark.parametrize(
        "symbol,expected_pair",
        [
            ("ETH", "ETH/USDT"),
            ("XRP", "XRP/USDT"),
        ],
    )
    @pytest.mark.base
    @pytest.mark.github
    def test_bitfinex_format_pair(self, bitfinex: Bitfinex, symbol: str, expected_pair: str):
        pair = format_pair(symbol, bitfinex.quote_currency, bitfinex.divider)
        assert pair == expected_pair
