import argparse
import asyncio
import json
import logging

from dotenv import load_dotenv
from flask import Flask, jsonify

from clients.binance import Binance
from clients.bybit import Bybit
from clients.exchange import Exchange
from clients.kraken import Kraken
from clients.bitfinex import Bitfinex
from config import Config
from loggers import setup_logging
from order_services import create_order, update_order
from parameters import add_common_args
from flask_mail import Mail

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

app = Flask(__name__)
load_dotenv()

parser = argparse.ArgumentParser()
parser = add_common_args(parser)
args = parser.parse_args()
env_name = args.env_name
config = Config(env_name=env_name)

# Read ccxt config from JSON file
file_path = "./exchanges_ccxt_config.json"
with open(file_path, "r") as file:
    exchanges_ccxt_config = json.load(file)

binance_ccxt_config = exchanges_ccxt_config["binance"]["ccxt_config"]
kraken_ccxt_config = exchanges_ccxt_config["kraken"]["ccxt_config"]
bitfinex_ccxt_config = exchanges_ccxt_config["bitfinex"]["ccxt_config"]
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
bitfinex = Bitfinex(
    config.bitfinex_api_key,
    config.bitfinex_secret,
    bitfinex_ccxt_config,
    exchanges_ccxt_config["config"],
)
bybit = Bybit(
    config.bybit_api_key,
    config.bybit_secret,
    bybit_ccxt_config,
    exchanges_ccxt_config["config"],
)

app.config["MAIL_SERVER"] = config.mail_server
app.config["MAIL_PORT"] = config.mail_port
app.config["MAIL_USE_TLS"] = config.mail_use_tls
app.config["MAIL_USERNAME"] = config.mail_username
app.config["MAIL_PASSWORD"] = config.mail_password
app.config["MAIL_DEFAULT_SENDER"] = config.mail_default_sender


mail = Mail(app)


@app.route("/create_order", methods=["POST"])
async def handle_create_order_request():
    results = []

    async def create_order_for_exchange(exchange: Exchange):
        exchange_name = exchange.exchange_name
        status = await create_order(config=config, exchange=exchange)
        results.append({"exchange": exchange_name, "status": "success" if status else "failed"})

    await asyncio.gather(
        create_order_for_exchange(binance),
        create_order_for_exchange(kraken),
        create_order_for_exchange(bitfinex),
        create_order_for_exchange(bybit),
    )

    success = all(result["status"] == "success" for result in results)
    if success:
        return jsonify({"status": "success", "message": "Orders created successfully", "results": results}), 200
    else:
        return jsonify({"status": "partial_success", "message": "Some orders failed", "results": results}), 207


@app.route("/update_order", methods=["POST"])
async def handle_update_order_request():
    results = []

    async def update_order_for_exchange(exchange: Exchange):
        exchange_name = exchange.exchange_name
        status = await update_order(config=config, exchange=exchange)
        results.append({"exchange": exchange_name, "status": "success" if status else "failed"})

    await asyncio.gather(
        update_order_for_exchange(binance),
        update_order_for_exchange(kraken),
        update_order_for_exchange(bitfinex),
        update_order_for_exchange(bybit),
    )
    success = all(result["status"] == "success" for result in results)
    if success:
        return jsonify({"status": "success", "message": "Orders updated successfully", "results": results}), 200
    else:
        return jsonify({"status": "partial_success", "message": "Some orders failed", "results": results}), 207


if __name__ == "__main__":
    logger.info(f"Running in {env_name} environment")
    app.run(host="0.0.0.0", port=8000, debug=True)
