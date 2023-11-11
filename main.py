import pandas as pd
import datetime
import os
import json
import websocket
import ta
from binance.client import Client
import importlib
import src.config_loader as config_loader
from src.markets_trader import BinanceTrader
import sys
import logging

#importlib.reload(markets_trader)

if len(sys.argv) != 4:
    logging.error('Usage: python main.py symbol_to_trade quantity_for_token')
else:
    symbol = sys.argv[1]
    quantity = sys.argv[2]
    max_lot_value = sys.argv[3]

config = config_loader.load_config('config.yaml')
api_key = config['API']['API_KEY']
api_secret = config['API']['API_SECRET']

symbol = 'DOGEUSDT'
quantity = 200
max_lot_value = 20

trader = BinanceTrader(api_key, api_secret, symbol,quantity, max_lot_value, '30m')
trader.run_forever()
trader.stream_df

def main():
    markets_trader.main(api_key, api_secret, symbol, quantity, max_lot_value)

if __name__ == "__main__":
    main()
