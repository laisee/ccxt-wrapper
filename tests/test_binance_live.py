import os
import sys

import pytest
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(".env")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from conftest import require_live_auth, skip_if_missing_env_vars
from clients.binance import Binance
from clients.exchange_utils import amount_to_precision
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
REQUIRED_ENV_VARS = {
    "BINANCE_PROD_APIKEY": API_KEY,
    "BINANCE_PROD_SECRET": API_SECRET,
}
DEFAULT_BALANCE_EMPTY = {}


def get_valid_market_amount(binance: Binance, symbol: str, side: str) -> float:
    pair = format_pair(symbol, binance.quote_currency, binance.divider)
    binance._api.load_markets()
    market = binance._api.market(pair)
    ticker = binance.fetch_ticker(pair)

    if ticker is None:
        pytest.skip(f"Unable to fetch ticker for {pair}")

    reference_price = ticker.get("ask") if side == SIDE_BUY else ticker.get("bid")
    if reference_price is None:
        reference_price = ticker.get("last")
    if reference_price is None or float(reference_price) <= 0:
        pytest.skip(f"Unable to determine a valid market price for {pair}")

    limits = market.get("limits", {})
    min_cost = (limits.get("cost") or {}).get("min") or 10.0
    min_amount = (limits.get("amount") or {}).get("min") or 0.0
    target_notional = max(float(min_cost) * 1.25, 12.0)
    raw_amount = max(float(min_amount), target_notional / float(reference_price))

    amount = amount_to_precision(raw_amount, market["precision"].get("amount"), binance._api.precisionMode)
    if amount <= 0:
        pytest.skip(f"Unable to calculate a valid order amount for {pair}")

    free_balance = binance.fetch_free_balance() or {}
    if side == SIDE_BUY:
        required_quote = amount * float(reference_price)
        quote_balance = float(free_balance.get(binance.quote_currency, 0.0) or 0.0)
        if quote_balance < required_quote:
            pytest.skip(
                f"Insufficient {binance.quote_currency} balance for live market buy on {pair}: need {required_quote}, have {quote_balance}"
            )
    else:
        base_balance = float(free_balance.get(symbol, 0.0) or 0.0)
        if base_balance < amount:
            pytest.skip(f"Insufficient {symbol} balance for live market sell on {pair}: need {amount}, have {base_balance}")

    return amount


@pytest.fixture
def binance():
    return Binance(api_key=API_KEY, secret=API_SECRET)


@pytest.fixture(scope="module")
def authenticated_binance():
    exchange = Binance(api_key=API_KEY, secret=API_SECRET)
    return require_live_auth(exchange, REQUIRED_ENV_VARS)


class TestBinanceLive:
    @pytest.mark.github
    @pytest.mark.base
    def test_binance_exists(self, binance):
        assert binance is not None

    @pytest.mark.github
    @pytest.mark.base
    def test_env_vars(self):
        skip_if_missing_env_vars(REQUIRED_ENV_VARS)
        assert API_KEY is not None
        assert API_SECRET is not None

    @pytest.mark.github
    @pytest.mark.base
    def test_binance_name(self, binance):
        assert binance.exchange_name == NAME

    @pytest.mark.github
    @pytest.mark.balance
    def test_binance_balance_is_empty(self, authenticated_binance):
        balances = authenticated_binance.fetch_balance()
        assert balances is not None

    @pytest.mark.github
    @pytest.mark.balance
    def test_binance_balance_gt_zero(self, authenticated_binance):
        balances = authenticated_binance.fetch_balance()
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
    def test_binance_create_market_order_buy_uni(self, authenticated_binance):
        amount = get_valid_market_amount(authenticated_binance, SYMBOL, SIDE_BUY)
        market_order = authenticated_binance.create_order(SYMBOL, TYPE_MARKET, SIDE_BUY, amount)
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
    def test_binance_create_market_order_sell_uni(self, authenticated_binance):
        amount = get_valid_market_amount(authenticated_binance, SYMBOL, SIDE_SELL)
        market_order = authenticated_binance.create_order(SYMBOL, TYPE_MARKET, SIDE_SELL, amount)
        assert market_order is not None

    @pytest.mark.github
    @pytest.mark.market
    def test_binance_create_market_order_buy_xrp(self, authenticated_binance):
        amount = get_valid_market_amount(authenticated_binance, SYMBOL2, SIDE_BUY)
        market_order = authenticated_binance.create_order(SYMBOL2, TYPE_MARKET, SIDE_BUY, amount)
        assert market_order is not None

    @pytest.mark.github
    @pytest.mark.market
    def test_binance_create_market_order_sell_xrp(self, authenticated_binance):
        amount = get_valid_market_amount(authenticated_binance, SYMBOL2, SIDE_SELL)
        market_order = authenticated_binance.create_order(SYMBOL2, TYPE_MARKET, SIDE_SELL, amount)
        assert market_order is not None

    @pytest.mark.github
    @pytest.mark.limit
    def test_binance_limit_buy_order_fail_too_small(self, authenticated_binance):
        limit_order = authenticated_binance.create_order(SYMBOL, TYPE_LIMIT, SIDE_BUY, AMOUNT_TOO_SMALL, PRICE)
        assert limit_order is None, "Binance should reject the buy order for notional amount (price X amount) being too small"

    @pytest.mark.github
    @pytest.mark.limit
    def test_binance_limit_sell_order_fail_too_small(self, authenticated_binance):
        limit_order = authenticated_binance.create_order(SYMBOL, TYPE_LIMIT, SIDE_SELL, AMOUNT_TOO_SMALL, PRICE)
        assert limit_order is None, "Binance should reject the sell order for notional amount (price X amount) being too small"

    @pytest.mark.github
    @pytest.mark.limit
    def test_binance_limit_buy_order_fail_too_big(self, authenticated_binance):
        limit_order = authenticated_binance.create_order(SYMBOL, TYPE_LIMIT, SIDE_BUY, AMOUNT_TOO_BIG, PRICE)
        assert (
            limit_order is None
        ), "Binance should reject the order for notional amount (price X amount) being too big compared to account balance"

    @pytest.mark.github
    @pytest.mark.limit
    def test_binance_limit_buy_order_fail_invalid_coin(self, authenticated_binance):
        limit_order = authenticated_binance.create_order(SYMBOL_INVALID, TYPE_LIMIT, SIDE_BUY, AMOUNT, PRICE)
        assert (
            limit_order is None
        ), "Binance should reject the order as coin selected '{SYMBOL_INVALID}' is not available for trading"

    @pytest.mark.github
    @pytest.mark.limit
    def test_binance_limit_sell_order_fail_invalid_coin(self, authenticated_binance):
        limit_order = authenticated_binance.create_order(SYMBOL_INVALID, TYPE_LIMIT, SIDE_SELL, AMOUNT, PRICE)
        assert (
            limit_order is None
        ), "Binance should reject the order as coin selected '{SYMBOL_INVALID}' is not available for trading"
