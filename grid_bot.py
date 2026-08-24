import os
from dotenv import load_dotenv
from binance.client import Client

#Get the key from the .env file
load_dotenv()
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")

#Authenticate to the Testnet
client = Client(api_key, api_secret, testnet=True)

#Pull live sandbox balance & BTC ticker
usdt_balance = client.get_asset_balance(asset = "USDT")
ticker = client.get_symbol_ticker(symbol="BTCUSDT")

current_price = float(ticker["price"])
free_usdt = float(usdt_balance["free"])

print(f"💰 Available USDT: ${free_usdt:.2f}")
print(f"📈 Current BTC Price: ${current_price:.2f}")

#Get our BTC fraction share and 1% steps for the grid bot
grid_step = 0.01
sell_level = current_price + current_price * grid_step
buy_level = current_price - current_price * grid_step

print(f"🟢 Buy Target:  ${buy_level:.2f}")
print(f"🔴 Sell Target: ${sell_level:.2f}")