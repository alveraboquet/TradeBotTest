import alpaca_trade_api as tradeapi
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import datetime
import requests
from yahoo_fin import stock_info as si
import time
import schedule
import sqlalchemy
import argparse
import sys
from os import system, name
import datetime as dt
import pickle
import __mysql as msql
import json
import threading
import concurrent.futures

api = tradeapi.REST('PKI9T8QMB3XFEB8IKY95', 'KzrlaRVyafuctfWqQ67jb4Q6CCrMhSumHfPPwITO', 'https://paper-api.alpaca.markets', api_version='v2')
clock = api.get_clock()

market_open_flag = False

top10 = [[]]
sell_list = [[]]

position_list = []
symbol_list = []

# INIT DEFAULTS
vars_dict = {'buy_counter': 0, 'sell_counter': 0, 'progression_counter': 0, 'regression_counter': 0,
             'stoploss_price': 0, 'buy_flag': False, 'sell_flag': False, 'progression_flag': False,
             'regression_flag': False,
             'is_owned': False, 'account_value': 100000, 'yearly_return': 0, 'order_id': 0}


def record_position_EMA(date, symbol, close, trend, position):
    try:
        # msql.insert_values(conn, table, 'date, symbol, position, price', f"'{date}', '{symbol}', '{position}', '{price}'")
        position_list.append([date, symbol, close, trend, position])
    except Exception as e:
        print(f"ERROR!\n{e}")


def record_position_SMA(date, symbol, sma5, sma30, close, variation, position):
    try:
        # msql.insert_values(conn, table, 'date, symbol, position, price', f"'{date}', '{symbol}', '{position}', '{price}'")
        position_list.append([date, symbol, sma5, sma30, close, variation, position])
    except Exception as e:
        print(f"ERROR!\n{e}")


def get_position_list():
    # print(position_list)
    poslist_df = pd.DataFrame(position_list)
    poslist_df.to_excel("POSLIST.xlsx")


def write_pickle(dict):
    filename = "tradebot_vars"
    outfile = open(filename, 'w+b')

    pickle.dump(dict, outfile)
    outfile.close()


def get_movingavg(stock):
    # INIT DEFAULTS
    # print(stock)

    vars_dict = {'buy_counter': 0, 'sell_counter': 0, 'progression_counter': 0, 'regression_counter': 0,
                 'stoploss_price': 0, 'buy_flag': False, 'sell_flag': False, 'progression_flag': False,
                 'regression_flag': False,
                 'is_owned': False, 'account_value': 100000, 'yearly_return': 0, 'order_id': 0}

    try:
        curr_price = si.get_live_price(stock)
    except (AssertionError, KeyError, json.decoder.JSONDecodeError, requests.urllib3.exceptions.ProtocolError, requests.exceptions.ChunkedEncodingError)  as e:
        return None

    stockprices = requests.get(
        f"https://financialmodelingprep.com/api/v3/historical-price-full/{stock}?serietype=line&apikey=992f4ace89c00105ff6c15b225372d70")
    stockprices = stockprices.json()

    if not stockprices:
        # print(f"{stock} RETURNED EMPTY")
        return None

    try:
        stockprices = stockprices['historical'][:60]
    except (AssertionError, KeyError, json.decoder.JSONDecodeError, requests.urllib3.exceptions.ProtocolError, requests.exceptions.ChunkedEncodingError) as e:
        return None

    stockprices = pd.DataFrame.from_dict(stockprices)
    stockprices = stockprices.set_index('date')

    stockprices['SMA_5d'] = stockprices['close'].rolling(5).mean()
    stockprices['SMA_30d'] = stockprices['close'].rolling(30).mean()

    var_this = 0
    var_last = 0

    iteration_count = 0

    for index, row in stockprices.iterrows():
        iteration_count += 1
        # print(f"VAR_THIS: {var_this} | VAR_LAST: {var_last}")

        date = index
        close = round(row[0], 2)
        sma5 = round(row[1], 2)
        sma30 = round(row[2], 2)

        var_buffer = close/sma5
        var_this = round((1-var_buffer)*-1, 2)

        # print(f"{stock} | TEST: VAR_THIS: {var_this} | VAR_LAST: {var_last}")

        if var_this > var_last:
            vars_dict['progression_counter'] += 1
            var_last = var_this
        elif var_this < var_last:
            vars_dict['regression_counter'] += 1
            var_last = var_this
        else:
            var_last = var_this

        # if not showing any progression or regression after 15 days, skip the stock
        if iteration_count == 15 and not vars_dict['progression_flag'] and not vars_dict['regression_flag']:
            break

        if vars_dict['progression_counter'] >= 7:
            print(f"{stock} | {date} | PROGRESSION")
            vars_dict['progression_flag'] = True
            record_position_SMA(date, stock, sma5, sma30, close, var_this, 'BUY')
            break

        elif vars_dict['regression_counter'] >= 3:
            # print(f"{stock} | {date} | REGRESSION")
            vars_dict['regression_flag'] = True
            # record_position_SMA(date, stock, sma5, sma30, close, var_this, 'SELL')
            break


    write_pickle(vars_dict)


def get_ema(stock):
    # INIT DEFAULTS

    vars_dict = {'buy_counter': 0, 'sell_counter': 0, 'progression_counter': 0, 'regression_counter': 0,
                 'stoploss_price': 0, 'buy_flag': False, 'sell_flag': False, 'progression_flag': False,
                 'regression_flag': False,
                 'is_owned': False, 'account_value': 100000, 'yearly_return': 0, 'order_id': 0}

    try:
        curr_price = si.get_live_price(stock)
    except (AssertionError, KeyError, json.decoder.JSONDecodeError, requests.urllib3.exceptions.ProtocolError, requests.exceptions.ChunkedEncodingError) as e:
        return None

    stockprices = requests.get(
        f"https://financialmodelingprep.com/api/v3/historical-price-full/{stock}?serietype=line&apikey=992f4ace89c00105ff6c15b225372d70")
    stockprices = stockprices.json()

    if not stockprices:
        # print(f"{stock} RETURNED EMPTY")
        return None

    try:
        stockprices = stockprices['historical'][:60]
    except KeyError as e:
        return None

    progression_counter = 0
    regression_counter = 0

    stockprices = pd.DataFrame.from_dict(stockprices)
    stockprices = stockprices.set_index('date')

    ema_short = stockprices['close'].ewm(span=5, adjust=False).mean()
    short_rolling = stockprices['close'].rolling(window=5).mean()

    stockprices['EMA'] = ema_short
    stockprices['SMA'] = short_rolling

    try:
        stockprices = stockprices.reindex(index=stockprices.index[::-1])
    except ValueError as e:
        if e:
            print(e)
            return None

    for date, row in stockprices.iterrows():

        close = round(row[0], 2)
        ema = round(row[1], 2)
        sma = round(row[2], 2)

        trend_this = round(close - ema, 2)

        if ema > sma and ema > close:
            progression_counter += 1

            if progression_counter >= 10:
                # top10.append([stock, trend_this])
                record_position_EMA(date, stock, close, trend_this, 'BUY')

        if ema < sma and ema < close:
            regression_counter += 1
            # record_position_EMA(date, stock, close, trend_this, 'SELL')

    if progression_counter > regression_counter:
        print(f"{threading.get_ident()} | {stock} final verdict is PROGRESSION")
    elif progression_counter < regression_counter:
        print(f"{threading.get_ident()} | {stock} final verdict is REGRESSION")


def get_variation():
    print("Getting variations...")

    only_buy_list = []
    nyse_data = pd.read_excel("POSLIST.xlsx", index_col=1)
    var_df = pd.DataFrame(nyse_data)
    var_df = var_df.drop(var_df.columns[0], 1)

    for index, row in var_df.iterrows():
        date = index
        symbol = row[1]
        sma5 = row[2]
        sma30 = row[3]
        close = row[4]
        variation = row[5]
        position = row[6]

        # only concern ourselves with progression indicated stocks
        if not 'BUY' in position:
            continue

        only_buy_list.append([date, symbol, sma5, sma30, variation])
        
    buylist_df = pd.DataFrame(only_buy_list)
    buylist_final = buylist_df.sort_values(by=[4], ascending=False)
    buylist_final = buylist_final.head(10)
    buylist_final.to_excel("BUY_LIST.xlsx", index=False)
