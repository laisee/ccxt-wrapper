import os
import sys

import pytest
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(".env")

# Note Using key from production environment. Only create LIVE orders in advanced test

# Add the parent folder to the system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from clients.exchange_utils import format_pair
from clients.kraken import Kraken

NAME = "kraken"
# Read API keys and secrets from environment variables
API_KEY = os.getenv("KRAKEN_PROD_APIKEY")
API_SECRET = os.getenv("KRAKEN_PROD_SECRET")
DEFAULT_BALANCE_EMPTY = {}
SYMBOL = "XRP"
SYMBOL_INVALID = "MOO"
SIDE_BUY = "buy"
SIDE_SELL = "sell"
TYPE_MARKET = "market"
TYPE_LIMIT = "limit"
AMOUNT = 1.00
AMOUNT_TOO_SMALL = AMOUNT / 1000.00
AMOUNT_TOO_BIG = AMOUNT * 1000000.00
PRICE = 6.00


@pytest.fixture
def kraken():
    return Kraken(api_key=API_KEY, secret=API_SECRET)


class TestKraken:
    @pytest.mark.base
    @pytest.mark.github
    def test_kraken_exists(self, kraken):
        assert kraken is not None

    @pytest.mark.base
    @pytest.mark.github
    def test_env_vars(self):
        assert API_KEY is not None
        assert API_SECRET is not None

    @pytest.mark.base
    @pytest.mark.github
    def test_kraken_name(self, kraken):
        assert kraken.exchange_name is not None
        assert kraken.exchange_name == NAME

    @pytest.mark.base
    @pytest.mark.github
    def test_kraken_balance_not_None(self, kraken):
        balances = kraken.fetch_balance()
        assert balances is not None

    @pytest.mark.balance
    @pytest.mark.github
    def test_kraken_balance_gt_zero(self, kraken):
        balances = kraken.fetch_balance()["info"]["result"]
        total = 0.00
        for bal in balances:
            assert float(balances[bal]["balance"]) >= 0.00  # account may have non-zero amount
            total += float(balances[bal]["balance"])
        assert (
            total >= 0.00
        ), f"Error while testing balance, s/be 0.00 was {total}"  # account should have some non-zero amounts

    @pytest.mark.base
    @pytest.mark.github
    @pytest.mark.parametrize("symbol", ["ETH", "BTC", "DOT", "SOL", "XRP"])
    def test_kraken_ticker(self, kraken: Kraken, symbol: str):
        pair = format_pair(symbol, kraken.quote_currency, kraken.divider)
        ticker = kraken.fetch_ticker(pair)
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
    def test_kraken_format_pair(self, kraken: Kraken, symbol: str, expected_pair: str):
        pair = format_pair(symbol, kraken.quote_currency, kraken.divider)
        assert pair == expected_pair

    @pytest.mark.market
    def test_kraken_market_order_buy(self, kraken):
        market_order = kraken.create_order(SYMBOL, TYPE_MARKET, SIDE_BUY, AMOUNT)
        assert market_order is not None

    @pytest.mark.market
    def test_kraken_market_order_sell(self, kraken):
        market_order = kraken.create_order(SYMBOL, TYPE_MARKET, SIDE_SELL, AMOUNT)
        assert market_order is not None

    @pytest.mark.market
    @pytest.mark.github
    def test_kraken_market_order_sell_fail_too_big(self, kraken):
        market_order = kraken.create_order(SYMBOL, TYPE_MARKET, SIDE_SELL, AMOUNT_TOO_BIG)
        assert market_order is None

    @pytest.mark.market
    @pytest.mark.github
    def test_kraken_market_order_sell_fail_too_small(self, kraken):
        market_order = kraken.create_order(SYMBOL, TYPE_MARKET, SIDE_SELL, AMOUNT_TOO_SMALL)
        assert market_order is None

    @pytest.mark.market
    @pytest.mark.github
    def test_kraken_market_order_sell_fail_invalid_coin(self, kraken):
        market_order = kraken.create_order(SYMBOL_INVALID, TYPE_MARKET, SIDE_SELL, AMOUNT)
        assert market_order is None

    @pytest.mark.limit
    @pytest.mark.github
    def test_kraken_limit_buy_order_fail_too_small(self, kraken):
        market_order = kraken.create_order(SYMBOL, TYPE_LIMIT, SIDE_BUY, AMOUNT_TOO_SMALL, PRICE)
        assert market_order is None, "Should FAIL due to order amount(price * amount) < Kraken min order amount"

    @pytest.mark.limit
    @pytest.mark.github
    def test_kraken_limit_sell_order_fail_too_small(self, kraken):
        market_order = kraken.create_order(SYMBOL, TYPE_LIMIT, SIDE_SELL, AMOUNT_TOO_SMALL, PRICE)
        assert market_order is None, "Should FAIL due to order amount(price * amount) < Kraken min order amount"

    @pytest.mark.limit
    @pytest.mark.github
    def test_kraken_limit_buy_order_fail_too_big(self, kraken):
        limit_order = kraken.create_order(SYMBOL, TYPE_LIMIT, SIDE_BUY, AMOUNT_TOO_BIG, PRICE)
        assert (
            limit_order is None
        ), "Kraken should reject the order for notional amount (price X amount) being too big compared to account balance"

    @pytest.mark.limit
    @pytest.mark.github
    def test_kraken_limit_buy_order_fail_invalid_coin(self, kraken):
        limit_order = kraken.create_order(SYMBOL_INVALID, TYPE_LIMIT, SIDE_BUY, AMOUNT, PRICE)
        assert (
            limit_order is None
        ), "Kraken should reject the order as coin selected '{SYMBOL_INVALID}' is not available for trading"

    @pytest.mark.limit
    @pytest.mark.github
    def test_kraken_limit_sell_order_fail_invalid_coin(self, kraken):
        limit_order = kraken.create_order(SYMBOL_INVALID, TYPE_LIMIT, SIDE_SELL, AMOUNT, PRICE)
        assert (
            limit_order is None
        ), "Kraken should reject the order as coin selected '{SYMBOL_INVALID}' is not available for trading"
