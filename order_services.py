import logging
import traceback
import psycopg

from decimal import Decimal

from dotenv import load_dotenv

from clients.exchange import Exchange
from config import Config
from database.models import Order, Trade
from enums import OrderSideValues, OrderTypeValues
from error_message import (
    INSUFFICIENT_BALANCE_BUY_ERROR,
    INSUFFICIENT_BALANCE_SELL_ERROR,
    MISSING_PRICE_ERROR,
    MISSING_TICKER_ERROR,
    UNKNOWN_ORDER_SIDE_ERROR,
    UNKNOWN_ORDER_TYPE_ERROR,
    VALIDATION_ERROR,
)
from email_services import send_insufficient_funds_email
from clients.exchange_utils import format_pair, amount_to_precision, price_to_precision

# Load environment variables from .env file
load_dotenv()
logger = logging.getLogger(__name__)


def validate_order(exchange: Exchange, pair: str, amount: float, price: float = None):
    market = exchange._api.market(pair)
    if not market:
        raise Exception(f"Market data not found for {pair}")

    # Extract limits

    limits = market["limits"]
    amount_limits = limits["amount"]
    price_limits = limits["price"]

    min_amount = amount_limits["min"]
    max_amount = amount_limits["max"]
    min_price = price_limits["min"]
    max_price = price_limits["max"]

    # Validate the order amount
    if amount < min_amount or (max_amount is not None and amount > max_amount):
        logger.error(f"Order amount {amount} is out of bounds: [{min_amount}, {max_amount}]")
        return False

    # Validate the order price
    if price and (price < min_price or price > max_price):
        logger.error(f"Order price {price} is out of bounds: [{min_price}, {max_price}]")
        return False

    return True


# TODO: prepare_order: calculate amount, round amount, price when generate order from signal
# def prepare_order(order, pair: str, exchange: Exchange):
#     ticker = exchange.fetch_ticker(pair)
#     if not ticker:
#         raise Exception(f"{MISSING_TICKER_ERROR}: {order}")

#     market = exchange._api.market(pair)
#     if not market:
#         raise Exception(f"Market data not found for {pair}")

#     average_price = ticker["average"]
#     amount = order["amount"]
#     price = order.get("price")
#     value = order.get("value")

#     calculated_amount = False
#     # If value is provided, calculate amount based on average price
#     if order["type"] == OrderTypeValues.MARKET and value and value > 0:
#         amount = value / Decimal(average_price)
#         calculated_amount = True

#     amount_rounded = amount_to_precision(amount, market["precision"]["amount"], exchange._api.precisionMode)
#     if price:
#         price_rounded = price_to_precision(price, market["precision"]["price"], exchange._api.precisionMode)

#     order["amount"] = amount_rounded
#     order["price"] = price_rounded if price else None

#     return order, average_price, calculated_amount


def process_order(
    exchange: Exchange,
    order,
    free_balance: dict,
    base_currency: str,
    quote_currency: str,
    average_price: float = None,
):
    side = order["side"]
    order_type = order["type"]
    amount = order["amount"]
    price = order.get("price")
    value = order.get("value")

    try:
        balance = None
        total_order_value = None
        balance_coin = None
        if side == OrderSideValues.BUY:
            if order_type == OrderTypeValues.MARKET:
                balance = free_balance.get(quote_currency, -1)
                total_order_value = value if value else amount * average_price
                balance_coin = quote_currency
                if balance < total_order_value:
                    raise Exception(f"{INSUFFICIENT_BALANCE_BUY_ERROR}: {order}")

                return exchange.create_order(
                    symbol=base_currency,
                    type=order_type,
                    side=side,
                    amount=amount,
                )
            elif order_type == OrderTypeValues.LIMIT:
                balance = free_balance.get(quote_currency, -1)
                total_order_value = amount * price
                balance_coin = quote_currency
                if not price:
                    raise Exception(f"{MISSING_PRICE_ERROR}: {order}")

                if balance < total_order_value:
                    raise Exception(f"{INSUFFICIENT_BALANCE_BUY_ERROR}: {order}")
                return exchange.create_order(
                    symbol=base_currency,
                    type=order_type,
                    side=side,
                    amount=amount,
                    price=price,
                )
            else:
                raise Exception(f"{UNKNOWN_ORDER_TYPE_ERROR}: {order}")
        elif side == OrderSideValues.SELL:
            balance = free_balance.get(base_currency, -1)
            total_order_value = amount
            balance_coin = base_currency
            if balance < total_order_value:
                raise Exception(f"{INSUFFICIENT_BALANCE_SELL_ERROR}: {order}")
            return exchange.create_order(
                symbol=base_currency,
                type=order_type,
                side=side,
                amount=amount,
                price=price,
            )
        else:
            raise Exception(f"{UNKNOWN_ORDER_SIDE_ERROR}: {order}")
    except Exception as e:
        if INSUFFICIENT_BALANCE_BUY_ERROR in str(e) or INSUFFICIENT_BALANCE_SELL_ERROR in str(e):
            send_insufficient_funds_email(order, exchange._api.name, balance, total_order_value, balance_coin)

        raise e


async def create_order(config: Config, exchange: Exchange):
    try:
        with psycopg.connect(config.conn_info) as conn:
            with conn.cursor() as cur:
                orders = Order.get_all_orders(
                    cur,
                    has_external_id=False,
                    status="open",
                    market_code=exchange.market_code,
                )
                for order in orders:
                    quote_currency = exchange.quote_currency
                    base_currency = order["coin_code"]

                    # total balance - used balance = free balance
                    # used balance: money on hold, locked, frozen, or pending, by currency
                    free_balance = exchange.fetch_free_balance()
                    pair = format_pair(base_currency, quote_currency, exchange.divider)

                    ticket = exchange.fetch_ticker(pair)
                    if not ticket:
                        raise Exception(f"{MISSING_TICKER_ERROR}: {order}")

                    average_price = ticket["average"]
                    # order, average_price, calculated_amount = prepare_order(order, pair, exchange)

                    if not validate_order(exchange, pair, order["amount"], order["price"]):
                        raise Exception(f"{VALIDATION_ERROR}: {order}")

                    # process order
                    order_info = process_order(exchange, order, free_balance, base_currency, quote_currency, average_price)
                    if not order_info:
                        continue

                    Order.update_order_by_id(
                        cur=cur,
                        external_order_id=order_info["id"],
                        id=order["id"],
                        filled_amount=order_info["filled"],
                        status=order_info["status"],
                    )
                    trades_for_order = order_info.get("trades")
                    if trades_for_order:
                        for trade in trades_for_order:
                            Trade.insert_trade_if_not_exists(
                                cur,
                                trade_id=trade["id"],
                                price=trade["price"],
                                quantity=trade["amount"],
                                timestamp=order_info["datetime"],
                                market_id=1,  # hardcode market id
                                order_id=order["id"],
                            )
        return True
    except Exception as e:
        logger.error(f"Failed to create orders: {e}")
        traceback.print_exc()
        return False


async def update_order(config: Config, exchange: Exchange):
    try:
        with psycopg.connect(config.conn_info) as conn:
            with conn.cursor() as cur:
                orders = Order.get_all_orders(
                    cur,
                    has_external_id=True,
                    status="open",
                    market_code=exchange.market_code,
                )
                if orders:
                    for order in orders:
                        order_info = exchange.fetch_order(
                            id=order["external_order_id"],
                            pair=order["coin_code"] + "USDT",
                        )
                        trades_for_order = exchange.get_trades_for_order(
                            order_id=order["external_order_id"],
                            pair=order["coin_code"] + "USDT",
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

                        Order.update_order_by_id(
                            cur=cur,
                            external_order_id=order_info["id"],
                            id=order["id"],
                            filled_amount=order_info["filled"],
                            status=order_info["status"],
                        )
        return True
    except Exception as e:
        logger.error(f"Failed to update orders: {e}")
        traceback.print_exc()
        return False
