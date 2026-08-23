import os
from dotenv import load_dotenv
from binance.client import Client

#Get the key from the .env file
load_dotenv()
key = os.getenv("API_KEY")
