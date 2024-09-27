from clients.exchange import Exchange


class Kraken(Exchange):
    def __init__(
        self,
        api_key,
        secret,
        ccxt_config: dict[str, any] = None,
        config: dict[str, any] = None,
    ):
        self.exchange_name = "kraken"
        self.market_code = "KRA-SPOT"
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
        pair = symbol + self.divider + self.quote_currency
        return super().create_order(pair, type, side, amount, price, params)
