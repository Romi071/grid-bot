import os
from dotenv import load_dotenv
from binance.client import Client

#Get the key from the .env file
load_dotenv()
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")

#Authenticate to the Testnet
client = Client(api_key, api_secret, testnet=True)

#Cancel all open orders to make the script safely runnable
client.cancel_all_open_orders(symbol="BTCUSDT")
print(client.get_open_orders(symbol="BTCUSDT"))

#Pull live sandbox balance & BTC ticker
usdt_balance = client.get_asset_balance(asset = "USDT")
ticker = client.get_symbol_ticker(symbol="BTCUSDT")

current_price = float(ticker["price"])
free_usdt = float(usdt_balance["free"])

print(f"💰 Available USDT: ${free_usdt:.2f}")
print(f"📈 Current BTC Price: ${current_price:.2f}")

#Define the n- buy and sell levels with grid steps of 1%
grid_step = 0.01
n = 3
buy_levels = []
sell_levels = []
for k in range(1, n+1):
    buy_levels.append(current_price * (1 - k * grid_step))
    sell_levels.append(current_price * (1 + k * grid_step))

#Order dispatching:
usdt_per_order = 15

#Buy loop
for price in buy_levels:
    buy_price = str(round(price, 2))
    btc_per_order = str(round(usdt_per_order / price, 5))

    order = client.order_limit_buy(
    symbol="BTCUSDT",
    quantity=btc_per_order,
    price=buy_price
    )

#Sell Loop
for price in sell_levels:
    sell_price = str(round(price, 2))
    btc_per_order = str(round(usdt_per_order / price, 5))

    order = client.order_limit_sell(
    symbol="BTCUSDT",
    quantity=btc_per_order,
    price=sell_price
    )