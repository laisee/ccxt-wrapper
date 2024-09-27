import ccxt

from typing import Any, Optional
from ccxt import decimal_to_precision, TRUNCATE, TICK_SIZE, ROUND

CcxtModuleType = Any


def is_exchange_known_ccxt(exchange_name: str, ccxt_module: Optional[CcxtModuleType] = None) -> bool:
    return exchange_name in ccxt_exchanges(ccxt_module)


def ccxt_exchanges(ccxt_module: Optional[CcxtModuleType] = None) -> list[str]:
    """
    Return the list of all exchanges known to ccxt
    """
    return ccxt_module.exchanges if ccxt_module is not None else ccxt.exchanges


def format_pair(symbol, quote_ccy, divider: None) -> str:
    return f"{symbol}{divider}{quote_ccy}"


def amount_to_precision(amount: float, amount_precision: Optional[float], precisionMode: Optional[int]) -> float:
    """
    Returns the amount to buy or sell to a precision the Exchange accepts

    :param amount: amount to truncate
    :param amount_precision: amount precision to use.
                             should be retrieved from markets[pair]['precision']['amount']
    :param precisionMode: precision mode to use. Should be used from precisionMode
                          one of ccxt's DECIMAL_PLACES, SIGNIFICANT_DIGITS, or TICK_SIZE
    :return: truncated amount
    """
    if amount_precision is not None and precisionMode is not None:
        precision = int(amount_precision) if precisionMode != TICK_SIZE else amount_precision
        # precision must be an int for non-ticksize inputs.
        amount = float(
            decimal_to_precision(
                amount,
                rounding_mode=TRUNCATE,
                precision=precision,
                counting_mode=precisionMode,
            )
        )

    return amount


def price_to_precision(
    price: float,
    price_precision: Optional[float],
    precisionMode: Optional[int],
    *,
    rounding_mode: int = ROUND,
) -> float:
    """
    Returns the price rounded to the precision the Exchange accepts.

    :param price: price to convert
    :param price_precision: price precision to use. Used from markets[pair]['precision']['price']
    :param precisionMode: precision mode to use. Should be used from precisionMode
                          one of ccxt's DECIMAL_PLACES, SIGNIFICANT_DIGITS, or TICK_SIZE
    :param rounding_mode: rounding mode to use. Defaults to ROUND
    :return: price rounded up to the precision the Exchange accepts
    """
    if price_precision is not None and precisionMode is not None:
        # Use CCXT code where possible.
        price = float(
            decimal_to_precision(
                price,
                rounding_mode=rounding_mode,
                precision=price_precision,
                counting_mode=precisionMode,
            )
        )
    return price
