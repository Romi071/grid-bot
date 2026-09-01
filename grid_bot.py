import requests
import os
import time
import json
from dotenv import load_dotenv
from binance.client import Client
from binance.exceptions import BinanceAPIException

#Get the key from the .env file
load_dotenv()
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")

#Authenticate to the Testnet client
client = Client(api_key, api_secret, testnet=True)

#Define the grid parameters and ticker
n = 30
grid_step = 0.01
usdt_per_order = 1000
trading_symbol = "BTCUSDT"

#Print live BTC ticker price
ticker = client.get_symbol_ticker(symbol=trading_symbol)
current_price = float(ticker["price"])
print(f"📈 Current {trading_symbol} Price: ${current_price:.2f}")


#Function to initialize a new grid and buy orders if the script has never been ran before
def initialize_new_grid():
    #Cancel all open orders to make the script safely runnable
    try:
        client.cancel_all_open_orders(symbol=trading_symbol)
    except Exception:
        pass

    #Define the n- initial buy levels
    buy_levels = [current_price * (1 - k * grid_step) for k in range(1, n+1)]

    #Initial buy loop and order dispatching
    init_active_orders = {}
    for price in buy_levels:
        buy_price = str(round(price, 2))
        btc_per_order = str(round(usdt_per_order / price, 5))

        order = client.order_limit_buy(
        symbol=trading_symbol,
        quantity=btc_per_order,
        price=buy_price
        )
        #Create a dictionary saving the active order IDs as the key and their buy price (negative) as their value 
        init_active_orders[order["orderId"]] = -float(order["price"])

    return init_active_orders

#Function to load existing the orders if the script has been ran previously
def load_existing_orders():
    with open("orders.json", "r") as file:
        return json.load(file)

#Function to save current bot state to the .json
def save_state(bot_state, cumul_profit, active_orders, vqueue):
    bot_state["profit"] = cumul_profit
    bot_state["active"] = active_orders
    bot_state["queue"] = vqueue
    with open("orders.json", "w") as file:
        json.dump(bot_state, file)

if os.path.exists("orders.json"):
    bot_state = load_existing_orders()
    cumul_profit = float(bot_state["profit"])
    active_orders = bot_state["active"]
    vqueue = bot_state["queue"]
    print(f"💵 Previous run detected, profits up until now: ${cumul_profit:.2f}")
else:
    active_orders = initialize_new_grid()
    cumul_profit = 0
    vqueue = []
    #Create a dictionary nesting the active orders dictionary, cumul profit variable, and virtual queue list, and dump it into a .json
    bot_state = {"profit": cumul_profit, "active": active_orders, "queue": vqueue}
    with open("orders.json", "w") as file:
        json.dump(bot_state, file)
    

#Print currently free and locked USDT and BTC balances
usdt_balance = client.get_asset_balance(asset = "USDT")
free_usdt = float(usdt_balance["free"])
locked_usdt = float(usdt_balance["locked"])
print(f"💰 Available USDT: ${free_usdt:.2f} free + ${locked_usdt:.2f} locked")

btc_balance = client.get_asset_balance(asset="BTC")
free_btc = float(btc_balance["free"])
locked_btc = float(btc_balance["locked"])
print(f"🥇 Available BTC: {free_btc:.4f} ₿ free + {locked_btc:.4f} ₿ locked")


#Infinite bot loop with error handling
error_count = 0
while True:
    try:
        #Ping Binance for ticker price, and my currently open orders with their IDs
        error_count = 0
        live_price = float(client.get_symbol_ticker(symbol=trading_symbol)["price"])
        open_orders = client.get_open_orders(symbol=trading_symbol)
        open_ids = [dictionary["orderId"] for dictionary in open_orders]
        for id in list(active_orders):
            #If an ID in my active orders dictionary is not currently open:
            if int(id) not in open_ids:
                #Check if the missing order is FILLED or cancelled/expired
                missing_order = client.get_order(symbol=trading_symbol, orderId=int(id))
                if missing_order["status"] == "FILLED":
                    #If a buy order was fulfilled place a sell order slightly above the original grid level
                    if active_orders[id] < 0:
                        id_price = -active_orders[id]
                        selling_price = str(round(id_price * (1 + grid_step), 2))
                        btc_per_order = str(round(0.999 * usdt_per_order / id_price, 5))

                        ordersell = client.order_limit_sell(
                        symbol=trading_symbol,
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
                        symbol=trading_symbol,
                        quantity=btc_per_order,
                        price=buying_price
                        )
                        
                        active_orders[orderbuy["orderId"]] = -id_price
                        active_orders.pop(id)
                        
                        #Net and Cumulative Profit tracker
                        net_profit = usdt_per_order * (grid_step - (0.001 + 0.001 * (1 + grid_step)))
                        cumul_profit += net_profit
                        print(f"💲💲💲 Sell order completed! Net profit gained: ${net_profit:.4f}. Total net profit made since start: {cumul_profit:.4f}")

                #The order is cancelled or expired and should be removed from active orders and into a virtual queue
                else:      
                    vqueue.append(active_orders[id])
                    active_orders.pop(id)

                #Update the .json file
                save_state(bot_state, cumul_profit, active_orders, vqueue)

        #Loop over the current virtual queue of cancelled orders to check if market is safe to place them
        for missing_price in list(vqueue):
            #If buy, check if buy price < BTC and place it
            if missing_price < 0 and -missing_price < live_price:
                buying_price = str(round(-missing_price, 2))
                btc_per_order = str(round(usdt_per_order / -missing_price, 5))

                orderbuy = client.order_limit_buy(
                symbol=trading_symbol,
                quantity=btc_per_order,
                price=buying_price
                )

                active_orders[orderbuy["orderId"]] = missing_price
                vqueue.remove(missing_price)

                #Update the .json file
                save_state(bot_state, cumul_profit, active_orders, vqueue)

            #If sell, check if selling price > BTC and place it
            elif missing_price > 0 and missing_price * (1 + grid_step) > live_price:
                selling_price = str(round(missing_price * (1 + grid_step), 2))
                btc_per_order = str(round(0.999 * usdt_per_order / missing_price, 5))

                ordersell = client.order_limit_sell(
                symbol=trading_symbol,
                quantity=btc_per_order,
                price=selling_price
                )

                active_orders[ordersell["orderId"]] = missing_price
                vqueue.remove(missing_price)

                #Update the .json file
                save_state(bot_state, cumul_profit, active_orders, vqueue)

        time.sleep(1)

#Error handling armor:
    #Connection error sleep 5 sec and try again
    except requests.exceptions.RequestException as error:
        print(f"\033[93m ⚠️ Loop execution failed due to the following network exception: {error} \033[0m")
        error_count += 1
        if error_count >= 20:
            print(f"\033[91m ❌ Too many consecutive errors. Exiting the program \033[0m")
            exit()
        time.sleep(5)
        continue

    #Binance Api error, identify error, sleep accordingly and try again:
    except BinanceAPIException as error:
        print(f"\033[93m ⚠️ Loop execution failed due to the following Binance API exception: {error} \033[0m")
        #Invalid API key or IP adress rejected. Unrecoverable error.
        if error.code in [-2014, -2015, -1022, -2010, -1013]:
            print(f"\033[91m ❌ Fatal API error. Exiting the program \033[0m")
            exit()
        #Timestamp out of sync
        elif error.code == -1021:
            time.sleep(5)
        #Rate limited
        elif error.code == -1003:
            time.sleep(70)
        #Mainteinance, 20min sleep
        else:
            time.sleep(1200)
        error_count += 1
        if error_count >= 20:
            print(f"\033[91m ❌ Too many consecutive errors. Exiting the program \033[0m")
            exit()
        continue

    #Unknown error maybe sleep 10 sec and try again
    except Exception as error:
        print(f"\033[93m ⚠️ Loop execution failed due to the following exception: {error} \033[0m")
        error_count += 1
        if error_count >= 20:
            print(f"\033[91m ❌ Too many consecutive errors. Exiting the program \033[0m")
            exit()
        time.sleep(10)
        continue