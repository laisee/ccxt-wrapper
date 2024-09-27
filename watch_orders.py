import argparse
import asyncio
import json
import logging
import traceback

import psycopg
from dotenv import load_dotenv

from clients.binance import Binance
from clients.bybit import Bybit
from clients.exchange import Exchange
from clients.kraken import Kraken
from config import Config
from database.models import Order, Trade
from loggers import setup_logging
from parameters import add_common_args

logger = logging.getLogger(__name__)


async def watch_orders(config: Config, exchange: Exchange):
    logger.info(f"Starting to watch orders for {exchange.__class__.__name__}...")
    while True:
        try:
            logger.info(f"Waiting for orders for {exchange.__class__.__name__}...")
            orders = await exchange.watch_orders()
            logger.info(f"Received orders for {exchange.__class__.__name__}: {orders}")
            with psycopg.connect(config.conn_info) as conn:
                with conn.cursor() as cur:
                    try:
                        for order_info in orders:
                            order = Order.get_order_by_external_order_id(
                                cur,
                                str(order_info["id"]),  # External Order Id
                            )

                            if order:
                                trades_for_order = exchange.get_trades_for_order(
                                    order_id=order["external_order_id"],
                                    pair=order_info["symbol"],  # Symbol
                                    since=order["created_on"],
                                )

                                if trades_for_order:
                                    for trade in trades_for_order:
                                        Trade.insert_trade_if_not_exists(
                                            cur,
                                            trade_id=trade["id"],
                                            price=trade["price"],
                                            quantity=trade["amount"],
                                            timestamp=trade["datetime"],
                                            market_id=1,  # hardcode market id
                                            order_id=order["id"],
                                        )

                                Order.update_order_by_external_order_id(
                                    cur=cur,
                                    external_order_id=order_info["id"],
                                    filled_amount=order_info["filled"],
                                    status=order_info["status"],
                                )
                    except Exception as e:
                        logger.error(f"Failed to update orders: {e}")
                        traceback.print_exc()

        except Exception as e:
            logger.error(f"Error in order listener: {e}")
            traceback.print_exc()


if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()
    setup_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser = add_common_args(parser)
    args = parser.parse_args()
    env_name = args.env_name
    config = Config(env_name=env_name)
    logger.info(f"Running in {env_name} environment")

    # Read ccxt config from JSON file
    file_path = "./exchanges_ccxt_config.json"
    with open(file_path, "r") as file:
        exchanges_ccxt_config = json.load(file)

    binance_ccxt_config = exchanges_ccxt_config["binance"]["ccxt_config"]
    kraken_ccxt_config = exchanges_ccxt_config["kraken"]["ccxt_config"]
    bybit_ccxt_config = exchanges_ccxt_config["bybit"]["ccxt_config"]

    binance = Binance(
        config.binance_api_key,
        config.binance_secret,
        binance_ccxt_config,
        exchanges_ccxt_config["config"],
    )
    kraken = Kraken(
        config.kraken_api_key,
        config.kraken_secret,
        kraken_ccxt_config,
        exchanges_ccxt_config["config"],
    )
    bybit = Bybit(
        config.bybit_api_key,
        config.bybit_secret,
        bybit_ccxt_config,
        exchanges_ccxt_config["config"],
    )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        asyncio.gather(
            watch_orders(config, binance),
            watch_orders(config, kraken),
            watch_orders(config, bybit),
        )
    )
