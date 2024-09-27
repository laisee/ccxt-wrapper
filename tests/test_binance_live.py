import os
import sys

import pytest
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(".env")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from clients.binance import Binance
from clients.exchange_utils import format_pair

# testing parameters for Binance exchange
NAME = "binance"
SYMBOL = "UNI"
SYMBOL2 = "XRP"
SYMBOL_INVALID = "MOO"
SIDE_BUY = "Buy"
SIDE_SELL = "Sell"
TYPE_MARKET = "market"
TYPE_LIMIT = "limit"
AMOUNT = 1.00

# following amount Generates an order valued at less than 0.0100 (taken from coin precision limit of 0.01)
# See error msg from Binance -> "binance amount of UNI/USDT must be greater than minimum amount precision of 0.01"
AMOUNT_TOO_SMALL = AMOUNT / 1000.00
# following amount will cause order to fail because its much larger than account balance
AMOUNT_TOO_BIG = AMOUNT * 1000.00

PRICE = 6.00
API_KEY = os.getenv("BINANCE_PROD_APIKEY")
API_SECRET = os.getenv("BINANCE_PROD_SECRET")
DEFAULT_BALANCE_EMPTY = {}


@pytest.fixture
def binance():
    return Binance(api_key=API_KEY, secret=API_SECRET)


class TestBinanceLive:
    @pytest.mark.github
    @pytest.mark.base
    def test_binance_exists(self, binance):
        assert binance is not None

    @pytest.mark.github
    @pytest.mark.base
    def test_env_vars(self):
        assert API_KEY is not None
        assert API_SECRET is not None

    @pytest.mark.github
    @pytest.mark.base
    def test_binance_name(self, binance):
        assert binance.exchange_name == NAME

    @pytest.mark.github
    @pytest.mark.balance
    def test_binance_balance_is_empty(self, binance):
        balances = binance.fetch_balance()
        assert balances is not None

    @pytest.mark.github
    @pytest.mark.balance
    def test_binance_balance_gt_zero(self, binance):
        balances = binance.fetch_balance()
        assert balances is not None, print(f"Error reading {type(balances)} response: {balances}")
        assert balances["info"]["balances"] is not None, print("Error retrieving balances from Binance")
        total = 0.00
        for balance in balances["info"]["balances"]:
            assert balance["asset"] is not None
            assert balance["free"] is not None
            assert balance["free"] is not None and float(balance["free"]) >= 0.00
            total += float(balance["free"])
        assert total >= 0.00

    @pytest.mark.github
    @pytest.mark.market
    def test_binance_create_market_order_buy_uni(self, binance):
        market_order = binance.create_order(SYMBOL, TYPE_MARKET, SIDE_BUY, AMOUNT)
        assert market_order is not None

    @pytest.mark.base
    @pytest.mark.github
    @pytest.mark.parametrize(
        "symbol,expected_pair",
        [
            (
                "ETH",
                "ETH/USDT",
            ),
            (
                "XRP",
                "XRP/USDT",
            ),
        ],
    )
    @pytest.mark.base
    @pytest.mark.github
    def test_binance_format_pair(self, binance: Binance, symbol: str, expected_pair: str):
        pair = format_pair(symbol, binance.quote_currency, binance.divider)
        assert pair == expected_pair

    @pytest.mark.github
    @pytest.mark.market
    def test_binance_create_market_order_sell_uni(self, binance):
        market_order = binance.create_order(SYMBOL, TYPE_MARKET, SIDE_SELL, AMOUNT * 0.999)
        assert market_order is not None

    @pytest.mark.github
    @pytest.mark.market
    def test_binance_create_market_order_buy_xrp(self, binance):
        market_order = binance.create_order(SYMBOL2, TYPE_MARKET, SIDE_BUY, AMOUNT * 10.00)
        assert market_order is not None

    @pytest.mark.github
    @pytest.mark.market
    def test_binance_create_market_order_sell_xrp(self, binance):
        market_order = binance.create_order(SYMBOL2, TYPE_MARKET, SIDE_SELL, AMOUNT * 9.99)
        assert market_order is not None

    @pytest.mark.github
    @pytest.mark.limit
    def test_binance_limit_buy_order_fail_too_small(self, binance):
        limit_order = binance.create_order(SYMBOL, TYPE_LIMIT, SIDE_BUY, AMOUNT_TOO_SMALL, PRICE)
        assert limit_order is None, "Binance should reject the buy order for notional amount (price X amount) being too small"

    @pytest.mark.github
    @pytest.mark.limit
    def test_binance_limit_sell_order_fail_too_small(self, binance):
        limit_order = binance.create_order(SYMBOL, TYPE_LIMIT, SIDE_SELL, AMOUNT_TOO_SMALL, PRICE)
        assert limit_order is None, "Binance should reject the sell order for notional amount (price X amount) being too small"

    @pytest.mark.github
    @pytest.mark.limit
    def test_binance_limit_buy_order_fail_too_big(self, binance):
        limit_order = binance.create_order(SYMBOL, TYPE_LIMIT, SIDE_BUY, AMOUNT_TOO_BIG, PRICE)
        assert (
            limit_order is None
        ), "Binance should reject the order for notional amount (price X amount) being too big compared to account balance"

    @pytest.mark.github
    @pytest.mark.limit
    def test_binance_limit_buy_order_fail_invalid_coin(self, binance):
        limit_order = binance.create_order(SYMBOL_INVALID, TYPE_LIMIT, SIDE_BUY, AMOUNT, PRICE)
        assert (
            limit_order is None
        ), "Binance should reject the order as coin selected '{SYMBOL_INVALID}' is not available for trading"

    @pytest.mark.github
    @pytest.mark.limit
    def test_binance_limit_sell_order_fail_invalid_coin(self, binance):
        limit_order = binance.create_order(SYMBOL_INVALID, TYPE_LIMIT, SIDE_SELL, AMOUNT, PRICE)
        assert (
            limit_order is None
        ), "Binance should reject the order as coin selected '{SYMBOL_INVALID}' is not available for trading"
