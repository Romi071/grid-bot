import os
import time
from dotenv import load_dotenv
from binance.client import Client

#Get the key from the .env file
load_dotenv()
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")

#Authenticate to the Testnet
client = Client(api_key, api_secret, testnet=True)

#Cancel all open orders to make the script safely runnable
try:
    client.cancel_all_open_orders(symbol="BTCUSDT")
except Exception:
    pass

#Pull live BTC ticker price
ticker = client.get_symbol_ticker(symbol="BTCUSDT")
current_price = float(ticker["price"])
print(f"📈 Current BTC Price: ${current_price:.2f}")

#Define the n- buy levels with grid steps of 1%
grid_step = 0.01
n = 30
buy_levels = [current_price * (1 - k * grid_step) for k in range(1, n+1)]

#Initial buy loop and order dispatching
usdt_per_order = 1000
cumul_profit = 0
active_orders = {}
for price in buy_levels:
    buy_price = str(round(price, 2))
    btc_per_order = str(round(usdt_per_order / price, 5))

    order = client.order_limit_buy(
    symbol="BTCUSDT",
    quantity=btc_per_order,
    price=buy_price
    )
    #Create a dictionary saving the active order IDs as the key and their buy price (negative) as their value 
    active_orders[order["orderId"]] = -float(order["price"])

#Print currently free and locked USDT and BTC balances
usdt_balance = client.get_asset_balance(asset = "USDT")
free_usdt = float(usdt_balance["free"])
locked_usdt = float(usdt_balance["locked"])
print(f"💰 Available USDT: ${free_usdt:.2f} free + ${locked_usdt:.2f} locked")

btc_balance = client.get_asset_balance(asset="BTC")
free_btc = float(btc_balance["free"])
locked_btc = float(btc_balance["locked"])
print(f"🥇 Available BTC: {free_btc:.2f} ₿ free + {locked_btc:.2f} ₿ locked")


#Infinite bot loop
while True:
    #Ping Binance for my currently open orders and their IDs
    open_orders = client.get_open_orders(symbol="BTCUSDT")
    open_ids = [dictionary["orderId"] for dictionary in open_orders]
    for id in list(active_orders):
        #If an ID in my active orders dictionary is not currently open:
        if id not in open_ids:
            #If a buy order was fulfilled place a sell order slightly above the original grid level
            if active_orders[id] < 0:
                id_price = -active_orders[id]
                selling_price = str(round(id_price * (1 + grid_step), 2))
                btc_per_order = str(round(0.999 * usdt_per_order / id_price, 5))

                ordersell = client.order_limit_sell(
                symbol="BTCUSDT",
                quantity=btc_per_order,
                price=selling_price
                )

                active_orders[ordersell["orderId"]] = id_price
                active_orders.pop(id)
            #If a sell order was fulfilled place a buy order at the original grid level
            else:
                id_price = active_orders[id]
                buying_price = str(round(id_price, 2))
                btc_per_order = str(round(usdt_per_order / id_price, 5))
                
                orderbuy = client.order_limit_buy(
                symbol="BTCUSDT",
                quantity=btc_per_order,
                price=buying_price
                )
                
                active_orders[orderbuy["orderId"]] = -float(orderbuy["price"])
                active_orders.pop(id)
                #Profit tracker
                net_profit = usdt_per_order * (grid_step - (0.001 + 0.001 * (1 + grid_step)))
                cumul_profit += net_profit
                print(f"💲💲💲 Sell order completed! Net profit gained: ${net_profit:.4f}. Total net profit made since start: {cumul_profit:.4f}")
                
    time.sleep(1)

