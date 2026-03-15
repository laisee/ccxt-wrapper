import os
import sys

import pytest
from dotenv import load_dotenv
from unittest.mock import patch

# Load environment variables from .env file
load_dotenv(".env")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from clients.binance import Binance
from clients.exchange_utils import amount_to_precision, format_pair, price_to_precision
from conftest import time_limit
from order_services import process_order, validate_order
from error_message import INSUFFICIENT_BALANCE_BUY_ERROR, INSUFFICIENT_BALANCE_SELL_ERROR

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

AMOUNT_TOO_BIG = AMOUNT * 1000000.00

PRICE = 6.00
API_KEY = os.getenv("BINANCE_TEST_APIKEY")
API_SECRET = os.getenv("BINANCE_TEST_SECRET")

CCXT_CONFIG = {"set_sandbox_mode": True}
DEFAULT_BALANCE_EMPTY = {}


def get_market_metadata(binance: Binance, symbol: str):
    pair = format_pair(symbol, binance.quote_currency, binance.divider)
    try:
        with time_limit(1):
            ticker = binance.fetch_ticker(pair)
    except TimeoutError:
        pytest.skip(f"Timed out loading market metadata for {pair}")

    if ticker is None:
        pytest.skip(f"Unable to fetch ticker for {pair}")

    try:
        market = binance._api.market(pair)
    except Exception:
        pytest.skip(f"Unable to load market metadata for {pair}")

    return pair, market, ticker


def get_valid_market_sell_amount(binance: Binance, symbol: str) -> float:
    pair, market, ticker = get_market_metadata(binance, symbol)
    bid_price = ticker.get("bid") or ticker.get("last")
    if bid_price is None or float(bid_price) <= 0:
        pytest.skip(f"Unable to determine a valid bid price for {pair}")

    limits = market.get("limits", {})
    min_cost = (limits.get("cost") or {}).get("min") or 10.0
    min_amount = (limits.get("amount") or {}).get("min") or 0.0
    raw_amount = max(float(min_amount), (float(min_cost) * 1.25) / float(bid_price))
    amount = amount_to_precision(raw_amount, market["precision"].get("amount"), binance._api.precisionMode)

    try:
        with time_limit(1):
            free_balance = binance.fetch_free_balance() or {}
    except TimeoutError:
        pytest.skip(f"Timed out fetching sandbox balance for {pair}")

    base_balance = float(free_balance.get(symbol, 0.0) or 0.0)
    if base_balance < amount:
        pytest.skip(f"Insufficient sandbox {symbol} balance for {pair}: need {amount}, have {base_balance}")

    return amount


def get_valid_limit_buy_params(binance: Binance, symbol: str) -> tuple[float, float]:
    pair, market, ticker = get_market_metadata(binance, symbol)
    ask_price = ticker.get("ask") or ticker.get("last")
    if ask_price is None or float(ask_price) <= 0:
        pytest.skip(f"Unable to determine a valid ask price for {pair}")

    price = price_to_precision(float(ask_price), market["precision"].get("price"), binance._api.precisionMode)
    limits = market.get("limits", {})
    min_cost = (limits.get("cost") or {}).get("min") or 10.0
    min_amount = (limits.get("amount") or {}).get("min") or 0.0
    raw_amount = max(float(min_amount), (float(min_cost) * 1.25) / float(price))
    amount = amount_to_precision(raw_amount, market["precision"].get("amount"), binance._api.precisionMode)

    try:
        with time_limit(1):
            free_balance = binance.fetch_free_balance() or {}
    except TimeoutError:
        pytest.skip(f"Timed out fetching sandbox balance for {pair}")

    quote_balance = float(free_balance.get(binance.quote_currency, 0.0) or 0.0)
    required_quote = amount * float(price)
    if quote_balance < required_quote:
        pytest.skip(
            f"Insufficient sandbox {binance.quote_currency} balance for {pair}: need {required_quote}, have {quote_balance}"
        )

    return amount, price


@pytest.fixture
def binance():
    return Binance(api_key=API_KEY, secret=API_SECRET, ccxt_config=CCXT_CONFIG)


class TestBinanceSandbox:
    @pytest.mark.base
    @pytest.mark.github
    def test_binance_exists(self, binance):
        assert binance is not None

    @pytest.mark.base
    @pytest.mark.github
    def test_env_vars(self):
        assert API_KEY is not None
        assert API_SECRET is not None

    @pytest.mark.base
    @pytest.mark.github
    def test_binance_name(self, binance):
        assert binance.exchange_name == NAME

    @pytest.mark.balance
    @pytest.mark.github
    def test_binance_balance_is_empty(self, binance):
        balances = binance.fetch_balance()
        assert balances is not None

    @pytest.mark.balance
    @pytest.mark.github
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

    @pytest.mark.market
    @pytest.mark.github
    def test_binance_market_sell_uni(self, binance):
        amount = get_valid_market_sell_amount(binance, SYMBOL)
        market_order = binance.create_order(SYMBOL, TYPE_MARKET, SIDE_SELL, amount)
        assert market_order is not None

    @pytest.mark.limit
    @pytest.mark.github
    def test_binance_limit_buy_order_success_uni(self, binance):
        amount, price = get_valid_limit_buy_params(binance, SYMBOL)
        limit_order = binance.create_order(SYMBOL, TYPE_LIMIT, SIDE_BUY, amount, price)
        assert limit_order is not None, f"Binance should accept buy order for {SYMBOL}"

    @pytest.mark.limit
    @pytest.mark.github
    def test_binance_limit_buy_order_success_xrp(self, binance):
        amount, price = get_valid_limit_buy_params(binance, SYMBOL2)
        limit_order = binance.create_order(SYMBOL2, TYPE_LIMIT, SIDE_BUY, amount, price)
        assert limit_order is not None, f"Binance should accept buy order for {SYMBOL2}"

    @pytest.mark.limit
    @pytest.mark.github
    def test_binance_limit_buy_order_fail_too_small(self, binance):
        limit_order = binance.create_order(SYMBOL, TYPE_LIMIT, SIDE_BUY, AMOUNT_TOO_SMALL, PRICE)
        assert limit_order is None, "Binance should reject the buy order for notional amount (price X amount) being too small"

    @pytest.mark.limit
    @pytest.mark.github
    def test_binance_limit_sell_order_fail_too_small(self, binance):
        limit_order = binance.create_order(SYMBOL, TYPE_LIMIT, SIDE_SELL, AMOUNT_TOO_SMALL, PRICE)
        assert limit_order is None, "Binance should reject the sell order for notional amount (price X amount) being too small"

    @pytest.mark.limit
    @pytest.mark.github
    def test_binance_limit_buy_order_fail_too_big(self, binance):
        limit_order = binance.create_order(SYMBOL, TYPE_LIMIT, SIDE_BUY, AMOUNT_TOO_BIG, PRICE)
        assert (
            limit_order is None
        ), "Binance should reject the order for notional amount (price X amount) being too big compared to account balance"

    @pytest.mark.limit
    @pytest.mark.github
    def test_binance_limit_buy_order_fail_invalid_coin(self, binance):
        limit_order = binance.create_order(SYMBOL_INVALID, TYPE_LIMIT, SIDE_BUY, AMOUNT, PRICE)
        assert (
            limit_order is None
        ), "Binance should reject the order as coin selected '{SYMBOL_INVALID}' is not available for trading"

    @pytest.mark.limit
    @pytest.mark.github
    def test_binance_limit_sell_order_fail_invalid_coin(self, binance):
        limit_order = binance.create_order(SYMBOL_INVALID, TYPE_LIMIT, SIDE_SELL, AMOUNT, PRICE)
        assert (
            limit_order is None
        ), "Binance should reject the order as coin selected '{SYMBOL_INVALID}' is not available for trading"

    @pytest.mark.base
    @pytest.mark.github
    @pytest.mark.parametrize("symbol", ["ETH", "BTC", "DOT", "XLM", "SOL", "XRP"])
    def test_binance_ticker(self, binance: Binance, symbol: str):
        pair = format_pair(symbol, binance.quote_currency, binance.divider)

        ticker = binance.fetch_ticker(pair)
        assert ticker is not None, f"Ticker {ticker}"
        assert float(ticker["ask"]) > 0.00
        assert float(ticker["bid"]) > 0.00
        assert float(ticker["high"]) > 0.00
        assert float(ticker["low"]) > 0.00

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
    def test_binance_format_pair(self, binance: Binance, symbol: str, expected_pair: str):
        pair = format_pair(symbol, binance.quote_currency, binance.divider)
        assert pair == expected_pair

    @pytest.mark.base
    @pytest.mark.github
    @patch("order_services.send_insufficient_funds_email")
    def test_insufficient_balance_buy(self, mock_send_email, binance: Binance):
        order_buy = {
            "id": "1",
            "side": "Buy",
            "type": "limit",
            "amount": 1.0,
            "price": 6.0,
            "coin_code": "UNI",
        }  # this is a mock order, order USDT for UNI at 6.0

        # mock the fetch_free_balance method to return a balance of 5.0 USDT
        with patch.object(binance, "fetch_free_balance", return_value={"USDT": 5.0}):
            with pytest.raises(Exception) as excinfo:
                process_order(binance, order_buy, binance.fetch_free_balance(), "UNI", "USDT")
            assert INSUFFICIENT_BALANCE_BUY_ERROR in str(excinfo.value)
            mock_send_email.assert_called_once()

    @pytest.mark.base
    @pytest.mark.github
    @patch("order_services.send_insufficient_funds_email")
    def test_insufficient_balance_sell(self, mock_send_email, binance: Binance):
        order_sell = {
            "id": "1",
            "side": "Sell",
            "type": "limit",
            "amount": 1.0,
            "price": 6.0,
            "coin_code": "UNI",
        }  # this is a mock order, sell 1.0 UNI
        # mock the fetch_free_balance method to return a balance of 0.0 UNI
        with patch.object(binance, "fetch_free_balance", return_value={"UNI": 0.0}):
            with pytest.raises(Exception) as excinfo:
                process_order(binance, order_sell, binance.fetch_free_balance(), "UNI", "USDT")
            assert INSUFFICIENT_BALANCE_SELL_ERROR in str(excinfo.value)
            mock_send_email.assert_called_once()

    @pytest.mark.base
    @pytest.mark.github
    def test_validate_order_valid(self, binance: Binance):
        pair = "UNI/USDT"
        amount = 1.0
        price = 6.0
        market = {
            "limits": {
                "amount": {"min": 0.1, "max": 10.0},
                "price": {"min": 1.0, "max": 100.0},
            },
            "precision": {"amount": 2, "price": 2},
        }
        # amount 1.0 is within the minimum and maximum amount limits of 0.1 and 10.0
        # price 6.0 is within the minimum and maximum price limits of 1.0 and 100.0
        with patch.object(binance._api, "market", return_value=market):
            assert validate_order(binance, pair, amount, price)

    @pytest.mark.base
    @pytest.mark.github
    def test_validate_order_invalid(self, binance: Binance):
        pair = "UNI/USDT"
        market = {
            "limits": {
                "amount": {"min": 0.1, "max": 10.0},
                "price": {"min": 1.0, "max": 100.0},
            },
            "precision": {"amount": 2, "price": 2},
        }

        with patch.object(binance._api, "market", return_value=market):
            # Test amount below min
            amount_below_min = 0.05
            price_valid = 6.0
            assert not validate_order(binance, pair, amount_below_min, price_valid)

            # Test amount above max
            amount_above_max = 20.0
            assert not validate_order(binance, pair, amount_above_max, price_valid)

            # Test price below min
            amount_valid = 1.0
            price_below_min = 0.5
            assert not validate_order(binance, pair, amount_valid, price_below_min)

            # Test price above max
            price_above_max = 200.0
            assert not validate_order(binance, pair, amount_valid, price_above_max)
