import os
import sys

import pytest
from dotenv import load_dotenv

load_dotenv(".env")
# Add the parent folder to the system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from clients.exchange_utils import format_pair
from clients.okx import OKX

NAME = "okx"
API_KEY = os.getenv("OKX_PROD_APIKEY")
API_SECRET = os.getenv("OKX_PROD_SECRET")
API_PASSPHRASE=os.getenv("OKX_PROD_PASSPHRASE")
CCXT_CONFIG = {"set_sandbox_mode": False}
EXCHANGE_CONFIG = {"password": API_PASSPHRASE}

@pytest.fixture
def okx():
    return OKX(API_KEY, API_SECRET, ccxt_config=CCXT_CONFIG, exchange_config=EXCHANGE_CONFIG)


class Testokx:
    @pytest.mark.base
    @pytest.mark.github
    def test_okx_exists(self, okx):
        assert okx is not None

    @pytest.mark.base
    @pytest.mark.github
    def test_env_vars(self):
        assert API_KEY is not None
        assert API_SECRET is not None

    @pytest.mark.base
    @pytest.mark.github
    def test_okx_name(self, okx):
        assert okx.exchange_name is not None
        assert okx.exchange_name == NAME

    @pytest.mark.base
    def test_okx_balance_not_None(self, okx):
        balances = okx.fetch_balance()
        assert balances is not None

    @pytest.mark.base
    @pytest.mark.github
    @pytest.mark.parametrize("symbol", ["ETH", "BTC", "DOT", "SOL", "XRP"])
    def test_okx_ticker(self, okx: okx, symbol: str):
        pair = format_pair(symbol, okx.quote_currency, okx.divider)
        ticker = okx.fetch_ticker(pair)
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
    def test_okx_format_pair(self, okx: okx, symbol: str, expected_pair: str):
        pair = format_pair(symbol, okx.quote_currency, okx.divider)
        assert pair == expected_pair
