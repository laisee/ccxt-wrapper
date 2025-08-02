import os


class Config:
    def __init__(self, env_name="dev"):
        self.env_name = env_name

        if self.env_name == "dev":
            binance_api_key = os.getenv("BINANCE_TEST_APIKEY")
            binance_secret = os.getenv("BINANCE_TEST_SECRET")
            kraken_api_key = os.getenv("KRAKEN_TEST_APIKEY")
            kraken_secret = os.getenv("KRAKEN_TEST_SECRET")
            bitfinex_api_key = os.getenv("BITFINEX_TEST_APIKEY")
            bitfinex_secret = os.getenv("BITFINEX_TEST_SECRET")
            bybit_api_key = os.getenv("BYBIT_TEST_APIKEY")
            bybit_secret = os.getenv("BYBIT_TEST_SECRET")

        elif self.env_name == "prod":
            binance_api_key = os.getenv("BINANCE_PROD_APIKEY")
            binance_secret = os.getenv("BINANCE_PROD_SECRET")
            kraken_api_key = os.getenv("KRAKEN_PROD_APIKEY")
            kraken_secret = os.getenv("KRAKEN_PROD_SECRET")
            bitfinex_api_key = os.getenv("BITFINEX_PROD_APIKEY")
            bitfinex_secret = os.getenv("BITFINEX_PROD_SECRET")
            bybit_api_key = os.getenv("BYBIT_PROD_APIKEY")
            bybit_secret = os.getenv("BYBIT_PROD_SECRET")
        else:
            raise ValueError("Invalid environment")

        # Set configuration variables
        self.binance_api_key = binance_api_key
        self.binance_secret = binance_secret
        self.kraken_api_key = kraken_api_key
        self.kraken_secret = kraken_secret
        self.bitfinex_api_key = bitfinex_api_key
        self.bitfinex_secret = bitfinex_secret
        self.bybit_api_key = bybit_api_key
        self.bybit_secret = bybit_secret

        db_host = os.getenv("db_host")
        db_name = os.getenv("db_name")
        db_user = os.getenv("db_user")
        db_password = os.getenv("db_password")
        db_schema = os.getenv("db_schema")

        self.conn_info = (
            f"host={db_host} dbname={db_name} user={db_user} password={db_password} options='-c search_path={db_schema}'"
        )

        # Email
        self.recipients = os.getenv("recipients", "").split(",")
        self.mail_server = os.getenv("mail_server")
        self.mail_port = os.getenv("mail_port")
        self.mail_use_tls = os.getenv("mail_use_tls")
        self.mail_username = os.getenv("mail_username")
        self.mail_password = os.getenv("mail_password")
        self.mail_default_sender = os.getenv("mail_default_sender")

        if not all(
            [
                self.binance_api_key,
                self.binance_secret,
                self.kraken_api_key,
                self.kraken_secret,
                self.bitfinex_api_key,
                self.bitfinex_secret,
                self.bybit_api_key,
                self.bybit_secret,
                db_host,
                db_name,
                db_user,
                db_password,
                self.conn_info,
            ]
        ):
            raise ValueError("Some environment variables are missing")
