import aiohttp
import asyncio
import json
from pathlib import Path


async def fetch_binance(session):
    url = "https://api.binance.com/api/v3/ticker/price"
    async with session.get(url) as response:
        data = await response.json()
        result = []
        for item in data:
            symbol = item["symbol"]
            price = float(item["price"])
            result.append({"symbol": symbol, "price": price})
        return result


async def fetch_okx(session):
    url = "https://www.okx.com/api/v5/market/tickers?instType=SPOT"
    async with session.get(url) as response:
        data = await response.json()
        if data["code"] == "0":
            result = []
            for item in data["data"]:
                symbol = item["instId"].replace("-", "")
                price = float(item["last"])
                result.append({"symbol": symbol, "price": price})
            return result
        else:
            return []


async def fetch_bybit(session):
    url = "https://api.bybit.com/v5/market/tickers?category=spot"
    async with session.get(url) as response:
        data = await response.json()
        if "result" in data and "list" in data["result"]:
            result = []
            for item in data["result"]["list"]:
                symbol = item["symbol"]
                price = float(item["lastPrice"])
                result.append({"symbol": symbol, "price": price})
            return result
        else:
            return []

async def save_to_file(data, filename):
    Path(filename).write_text(json.dumps(data, indent=4))

def load_from_file(filename):
    return json.loads(Path(filename).read_text())


def find_common_coins(binance_data, okx_data, bybit_data):
    binance_symbols = set(item["symbol"] for item in binance_data)
    okx_symbols = set(item["symbol"] for item in okx_data)
    bybit_symbols = set(item["symbol"] for item in bybit_data)

    common_symbols = binance_symbols & okx_symbols & bybit_symbols
    return list(common_symbols)

def calculate_spread(binance_data, okx_data, bybit_data, common_symbols, spread_threshold=30):
    result = []
    for symbol in common_symbols:
        binance_price = None
        okx_price = None
        bybit_price = None

        for item in binance_data:
            if item["symbol"] == symbol:
                binance_price = item["price"]
                break

        for item in okx_data:
            if item["symbol"] == symbol:
                okx_price = item["price"]
                break

        for item in bybit_data:
            if item["symbol"] == symbol:
                bybit_price = item["price"]
                break

        if None not in (binance_price, okx_price, bybit_price):
            prices = {"Binance": binance_price, "OKX": okx_price, "Bybit": bybit_price}
            min_price = min(prices.values())
            max_price = max(prices.values())
            spread = ((max_price - min_price) / min_price) * 100

            if spread >= spread_threshold:
                result.append({"symbol": symbol, "spread": spread, "prices": prices})
    return result


async def main():
    async with aiohttp.ClientSession() as session:
        binance_data = await fetch_binance(session)
        okx_data = await fetch_okx(session)
        bybit_data = await fetch_bybit(session)

        await save_to_file(binance_data, "binance.json")
        await save_to_file(okx_data, "okx.json")
        await save_to_file(bybit_data, "bybit.json")

        binance_data = load_from_file("binance.json")
        okx_data = load_from_file("okx.json")
        bybit_data = load_from_file("bybit.json")

        common_symbols = find_common_coins(binance_data, okx_data, bybit_data)
        print(f"Общие монеты: {common_symbols}")

        results = calculate_spread(binance_data, okx_data, bybit_data, common_symbols, spread_threshold=30)

        for result in results:
            print(f"Монета: {result['symbol']}, Спред: {result['spread']:.2f}%")
            print(f"Цены: {result['prices']}")



asyncio.run(main())
