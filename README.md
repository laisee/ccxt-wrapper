# Moolah Trading
[![Python CI](https://github.com/moolah-finance/moolah-trading/actions/workflows/python-app.yml/badge.svg)](https://github.com/moolah-finance/moolah-trading/actions/workflows/python-app.yml)[![Security Check](https://github.com/moolah-finance/moolah-trading/actions/workflows/main.yml/badge.svg)](https://github.com/moolah-finance/moolah-trading/actions/workflows/main.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-311/)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-312/)

### Library for executing buy/sell orders and reporting on exchange account balances


```bash
conda create -n moolah-trading python=3.11
```

```bash
conda activate moolah-trading
```

```bash
pip install poetry
poetry install
```

| id | name             | ccxt_support | ccxt_sandbox_mode_support | ccxt_pro_support           | implemented                     |
|----|------------------|--------------|---------------------------|----------------------------|---------------------------------|
| 1  | binance          | ✅            | ✅                         | ✅                          | binance-spot (limit, market)    |
| 2  | bitfinex         | ✅            | ❌                         | ✅(not support watchOrders) |                                 |
| 3  | kraken           | ✅            | ❌                         | ✅                          |                                 |
| 4  | krakenfutures    | ✅            | ✅                         | ✅                          | kraken-futures (limit, market)  |
| 5  | bybit            | ✅            | ✅                         | ✅                          |                                 |
| 6  | coinbase         | ✅            | ❌                         | ✅                          |                                 |
| 7  | coinbaseexchange | ✅            | ✅                         | ✅                          |                                 |
| 8  | pancake swap     | ❌            |                           |                            |                                 |
| 9  | uniswap          | ❌            |                           |                            |                                 |
| 10 | deribit          | ✅            | ✅                         | ✅                          |                                 |
| 11 | curve            | ❌            |                           |                            |                                 |
| 12 | sushi            | ❌            |                           |                            |                                 |

|         |         | Spot Trading |        | Futures Trading  |
|---------|---------|--------------|--------|------------------|
|         |         | limit        | market |                  |
| binance | sandbox | ✅            | ✅      | ✅                |
|         | live    | ✅           | ✅     | ℹ️               |
| kraken  | sandbox | ❌            | ❌      | ✅                |
|         | live    | ✅           | ✅     | ℹ️               |
| bitfinex| paper   | ✅            | ✅      | ✅                |
|         | live    | ℹ️           | ℹ️     | ℹ️               |
| bybit   | sandbox | ✅            | ✅      | ✅                |
|         | live    | ℹ️           | ℹ️     | ℹ️               |
| gateio  | sandbox | ❌            | ❌      | ✅                |
|         | live    | ✅           | ✅     | ✅               |
| okx     | sandbox | ✅            | ✅      | ✅                |
|         | live    | ℹ️           | ℹ️     | ℹ️               |

✅	supports

❌	not support

ℹ️	not checked

API server: 
- Retrieve Orders from Moolah DB and create Orders on Exchange (create_order)
- In case out of sync, can manually update Orders status by running api update_order

```bash
python app.py
```


Create WebSocket connection to sync status of Orders on Exchange and Orders in Moolah DB 
```bash
python watch_orders.py
```

Docker
```bash
docker compose up -d
```

Ruff
```bash
ruff check .
```
