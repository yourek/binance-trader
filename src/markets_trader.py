import pandas as pd
import datetime
import os
import json
import websocket
import ta
import src.config_loader
from binance.client import Client
import importlib
import sys
import logging 
import time
import win32api


# config = config_loader.load_config('config.yaml')
# api_key = config['API']['API_KEY']
# api_secret = config['API']['API_SECRET']

# symbol = 'DOGEUSDT'
# quantity = 200
# max_lot_value = 20

class BinanceTrader:

    def __init__(self, api_key, api_secret, symbol, quantity, max_lot_value, period):
        self.client = Client(api_key, api_secret, testnet=False, tld='com')
        self.symbol = symbol
        self.period = period
        self.quantity = quantity
        self.subset_of_columns = ['open_time','close_time','open','close', 'high','low','volume','number_trades']
        self.socket = f'wss://fstream.binance.com/ws/{symbol.lower()}@kline_{period.lower()}'
        self.last_msg = {}
        self.stream_df = self.prepare_historical_data()

    def prepare_historical_data(self):
        klines = self.client.get_historical_klines(self.symbol, self.period, limit=365)
        historical = pd.DataFrame(klines)
        historical_columns = ['open_time', 'open', 'high', 'low', 'close', 
        'volume', 'close_time', 'asset_volume', 'number_trades', 'buy_volume', 'buy_quote', 'ignore']
        historical.columns=historical_columns
        historical = historical[self.subset_of_columns]
        historical.low = historical.low.astype(float)
        historical.high = historical.high.astype(float)
        historical.open = historical.open.astype(float)
        historical.close = historical.close.astype(float)
        historical = self.calculate_indicators(historical)
        
        return historical

    def calculate_indicators(self, df_to_update):
        df = df_to_update
        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        df['ema_25'] = ta.trend.EMAIndicator(close=df['close'], window=25).ema_indicator()
        df['ema_50'] = ta.trend.EMAIndicator(close=df['close'], window=50).ema_indicator()
        return df_to_update

    def add_new_period_to_historical(self, df, row):
        df = df.iloc[1:]
        new_row = row
        new_row['rsi'] = None
        new_row['ema_25'] = None
        new_row['ema_50'] = None
        df = pd.concat([df, new_row])
        return self.calculate_indicators(df)

    def place_order_buy(self):
        order = self.client.order_market_buy(symbol=self.symbol,quantity=self.quantity)
        return order

    def place_order_sell(self):
        order = self.client.order_market_sell(symbol=self.symbol,quantity=self.quantity)
        return order

    def features_create_order(self, side):
        order = client.futures_create_order(
            symbol=self.symbol,
            side=side.upper(),
            type='MARKET',
            quantity=self.quantity,
            leverage=10,
        )

    def format_numbers_row(self, row):
        row.open = row.open.astype(float)
        row.close = row.close.astype(float)
        row.high = row.high.astype(float)
        row.low = row.low.astype(float)
        return row

    def check_if_api_connection(self):
        try:
            self.client.get_account_snapshot(type='SPOT')
            return True
        except Exception as e:
            logging.error(e)
            return False

    def check_if_max_lot_value_true(self) -> bool:
        coin_info = self.client.get_all_tickers()
        df = pd.DataFrame(coin_info)
        df = df[df['symbol'] == self.symbol]
        value_for_given_quantity = float(df['price'].values[0]) * self.quantity  # Convert to float and select the first element
        
        if value_for_given_quantity <= max_lot_value:
            return True

        logging.error('Given lot size is exceeding your maximum value to trade with')
        return False

    def trader(self, df):
        previous_row = df.iloc[-2]
        current_row = df.iloc[-1]

        if (current_row.ema_25 > current_row.ema_50) and (previous_row.ema_25 < previous_row.ema_50):
            self.place_order_buy()
            print('bought' + datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        elif (current_row.ema_25 < current_row.ema_50) and (previous_row.ema_25 > previous_row.ema_50):
            self.place_order_sell()
            print('sold' + datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

    def on_message(self, ws, message):
        try:
            msg = json.loads(message)
            k = msg['k']
            row = pd.DataFrame(data=k, index=[0])
            row = row[['t','T','o','c','h','l','v','n']]
            row.columns = self.subset_of_columns
            row = self.format_numbers_row(row)

            if (self.last_msg == {}) or (k['T'] != self.last_msg['T']):
                self.last_msg = k
                self.stream_df = self.add_new_period_to_historical(self.stream_df, row)
                self.trader(self.stream_df)
        except Exception as e:
            logging.error(f'Error {e} while on_mesage()')
            ws.close()

    def on_error(ws, err):
        logging.error(err)
        ws.close()

    def on_close(ws, close_status_code, close_msg):
        logging.info('### closed ###')
        ws.run_forever()

    def on_open(ws):
        print('### opened ###')
        logging.info('### opened ###')

    def run_forever(self):
        print('running')
        ws = websocket.WebSocketApp(self.socket,
            on_open=self.on_open,
            on_error=self.on_error,
            on_message=self.on_message,
            on_close=self.on_close)

        try:
            ws.run_forever()
        except KeyboardInterrupt:
            pass