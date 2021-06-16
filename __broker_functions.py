import alpaca_trade_api as tradeapi
import pandas as pd
import datetime
import requests
import math
from yahoo_fin import stock_info as si
import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import threading
import concurrent.futures
import __math_functions as mf


api = tradeapi.REST('PKI9T8QMB3XFEB8IKY95', 'KzrlaRVyafuctfWqQ67jb4Q6CCrMhSumHfPPwITO', 'https://paper-api.alpaca.markets', api_version='v2')
top10 = [[]]
sell_list = [[]]
sell_mode = False

symbol_list = []


def buy_order(symbol, qty):
    # templist = ['VCRA', 'TUP', 'JMIA', 'HUYA', 'HOME', 'HBB', 'EBS', 'BXC', 'ASA', 'ARLO', 'AAPL']
    portfolio_stocks = []
    portfolio2 = api.list_positions()
    for position in portfolio2:
        portfolio_stocks.append(position.symbol)

    print(f"Portfolio: {portfolio_stocks}")
    # print(f"Portfolio: {portfolio_stocks}")

    if symbol not in portfolio_stocks:
        print(f"{symbol} not found in portfolio...sending buy order")
        # api.submit_order(symbol=symbol, qty=qty, side='buy', type='market', time_in_force='gtc')
    else:
        print(f"{symbol} exists in portfolio...skipping")


def sell_order(symbol):
    selllist = [[]]
    now = datetime.datetime.now()
    qty = 0
    portfolio = api.list_positions()
    for positions in portfolio:
        if symbol in positions.symbol:
            qty = positions.qty
            selllist.append(symbol, qty)
    selllist_df = pd.DataFrame(selllist)
    selllist_df.to_excel(f'{now.strftime("%Y%m%d%H%m")}_selllist.xlsx')
    curr_price = round(si.get_live_price(symbol), 2)
    print(f"Selling {qty} of {symbol}")
    # api.submit_order(symbol=symbol, qty=qty, side='sell', type='limit', time_in_force='opg', limit_price=curr_price)
    sell_mode = False


def get_positions():
    print(f"Getting positions...")
    portfolio1 = api.list_positions()

    for position in portfolio1:
        if not position:
            print(f"No positions noted...moving on")
            return None
        else:
            mf.get_movingavg(position.symbol, 1)


def close_positions():
    print(f"Closing positions...")
    sell_mode = True
    if len(sell_list) == 0:
        print(f"Nothing in sell list...moving on \n\n")
        return None

    for symbol in sell_list:
        if not symbol:
            continue

        print(f"SYMBOL: {symbol[0]} | VAR: {symbol[1]}")

        sell_order(symbol[0])

def get_account():
    account = api.get_account()
    portfolio = api.list_positions()

    print('[+] ACCOUNT NUMBER: ' + account.account_number)
    print('[+] ACCOUNT CASH: ' + account.cash)
    print('[+] PORTFOLIO VALUE: ' + account.portfolio_value + '\n')

def is_open():
    clock = api.get_clock()

    return clock.is_open