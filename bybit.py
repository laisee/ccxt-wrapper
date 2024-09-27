from clients.exchange import Exchange
from clients.exchange_utils import format_pair


class Bybit(Exchange):
    def __init__(
        self,
        api_key,
        secret,
        ccxt_config: dict[str, any] = None,
        config: dict[str, any] = None,
    ):
        self.exchange_name = "bybit"
        self.market_code = "BYB-SPOT"
        self.quote_currency = "USDT"
        self.divider = "/"
        super().__init__(self.exchange_name, api_key, secret, ccxt_config, config)

    def create_order(
        self,
        symbol: str,
        type: str,
        side: str,
        amount: float,
        price=None,
        params=None,
    ):
        pair = format_pair(symbol, self.quote_currency, self.divider)
        return super().create_order(pair, type, side, amount, price, params)
