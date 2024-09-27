import logging
from datetime import datetime, timezone
from typing import Any, Optional

import ccxt
import ccxt.pro as ccxt_pro

from clients.exchange_utils import is_exchange_known_ccxt
from clients.types import Ticker

logger = logging.getLogger(__name__)


class Exchange:
    def __init__(
        self,
        exchange_name,
        api_key,
        secret,
        ccxt_config: dict[str, Any] = None,
        config: dict[str, Any] = None,
        exchange_config: dict[str, Any] = None,
    ):
        self._api: ccxt.Exchange
        self._ws_async: ccxt_pro.Exchange = None
        self._api = self._init_ccxt(exchange_name, api_key, secret, True, ccxt_config, exchange_config)
        self._ws_async = self._init_ccxt(exchange_name, api_key, secret, False, ccxt_config, exchange_config)
        self.market_code: str
        self.quote_currency: str
        self.divider: str
        self.config = config if config else {}
        self.log_responses = self.config.get("log_responses", False)

    def _init_ccxt(
        self,
        exchange_name: str,
        api_key: str,
        secret: str,
        sync: bool,
        ccxt_config: dict[str, Any],
        exchange_config: dict[str, Any],
    ) -> ccxt.Exchange:
        """
        Initialize ccxt with given config and return valid ccxt instance.
        """
        # Find matching class for the given exchange name
        if sync:
            ccxt_module = ccxt
        else:
            ccxt_module = ccxt_pro
        if not is_exchange_known_ccxt(exchange_name, ccxt_module):
            raise Exception(f"Exchange {exchange_name} is not supported by ccxt")

        if exchange_config is None:
            exchange_config = {}

        ex_config = {
            "apiKey": api_key,
            "secret": secret,
            "password": exchange_config.get("password", None),
        }

        try:
            api = getattr(ccxt_module, exchange_name.lower())(ex_config)
            if ccxt_config:
                for key, value in ccxt_config.items():
                    if hasattr(api, key):
                        method = getattr(api, key)
                        method(value)
                    else:
                        logger.warning(f"Unknown configuration key: {key}")
        except (KeyError, AttributeError) as e:
            raise Exception(f"Exchange {exchange_name} is not supported") from e
        except ccxt.BaseError as e:
            raise Exception(f"Initialization of ccxt failed. Reason: {e}") from e

        return api

    def _log_exchange_response(self, endpoint: str, response, *, add_info=None) -> None:
        """Log exchange responses"""
        if self.log_responses:
            add_info_str = "" if add_info is None else f" {add_info}: "
            logger.info(f"API {endpoint}: {add_info_str}{response}")

    def create_order(
        self,
        pair: str,
        type: str,
        side: str,
        amount: float,
        price=None,
        params: Optional[dict] = None,
    ) -> dict:
        try:
            if params is None:
                params = {}

            # limit needs price, market doesn't need price
            price = price if type == "limit" else None

            order = self._api.create_order(pair, type, side, amount, price, params)
            self._log_exchange_response("create_order", order)

            return order
        except ccxt.BaseError as e:
            logger.error(f"Failed to create order on {self._api.name}: {e}")
            return None

    def fetch_balance(self, params: Optional[dict] = None):
        try:
            if params is None:
                params = {}
            return self._api.fetch_balance(params)
        except ccxt.BaseError as e:
            logger.error(f"Failed to fetch balance from {self._api.name}: {e}")
            return None

    def fetch_free_balance(self, params: Optional[dict] = None):
        try:
            if params is None:
                params = {}
            balance = self._api.fetch_free_balance(params)
            return balance
        except ccxt.BaseError as e:
            logger.error(f"Failed to fetch free balance from {self._api.name}: {e}")
            return None

    def fetch_order(self, id: str, pair: str, params: Optional[dict] = None):
        try:
            if params is None:
                params = {}
            order = self._api.fetch_order(id, pair, params)
            self._log_exchange_response("fetch_order", order)
            return order
        except ccxt.BaseError as e:
            logger.error(f"Failed to fetch order from {self._api.name}: {e}")
            return None

    def fetch_ticker(self, pair: str) -> Ticker:
        try:
            data = self._api.fetch_ticker(pair)
            return data

        except ccxt.BaseError as e:
            logger.error(f"Failed to fetch ticker from {self._api.name}: {e}")
            return None

    def get_trades_for_order(self, order_id: str, pair: str, since: datetime, params: Optional[dict] = None) -> list:
        """
        Fetch Orders using the "fetch_my_trades" endpoint and filter them by order-id.
        The "since" argument passed in is coming from the database and is in UTC,
        as timezone-native datetime object.
        From the python documentation:
            > Naive datetime instances are assumed to represent local time
        Therefore, calling "since.timestamp()" will get the UTC timestamp, after applying the
        transformation from local timezone to UTC.
        This works for timezones UTC+ since then the result will contain trades from a few hours
        instead of from the last 5 seconds, however fails for UTC- timezones,
        since we're then asking for trades with a "since" argument in the future.

        :param order_id order_id: Order-id as given when creating the order
        :param pair: Pair the order is for
        :param since: datetime object of the order creation time. Assumes object is in UTC.
        """
        try:
            if params is None:
                params = {}
            my_trades = self._api.fetch_my_trades(
                pair,
                int((since.replace(tzinfo=timezone.utc).timestamp() - 5) * 1000),
                params=params,
            )
            matched_trades = [trade for trade in my_trades if trade["order"] == order_id]
            self._log_exchange_response("get_trades_for_order", matched_trades)
            return matched_trades
        except ccxt.BaseError as e:
            logger.error(f"Failed to retrieve matching trades on {self._api.name}: {e}")
            return None

    async def watch_orders(self, symbol: str = None, since: datetime = None, limit: int = None, params=None) -> list:
        if params is None:
            params = {}
        if since:
            since = (int((since.replace(tzinfo=timezone.utc).timestamp() - 5) * 1000),)

        orders = await self._ws_async.watch_orders(
            symbol,
            since,
            limit,
            params,
        )

        return orders
