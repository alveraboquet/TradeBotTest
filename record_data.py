import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import alpaca_trade_api as tradeapi
import pandas as pd
import requests
import numpy as np
import datetime as dt
import time
import json
from os import system, name
import sqlite3
from sqlite3 import Error
import argparse
import sys
import sqlalchemy
import __mysql as msql

api = tradeapi.REST('PKI9T8QMB3XFEB8IKY95', 'KzrlaRVyafuctfWqQ67jb4Q6CCrMhSumHfPPwITO', 'https://paper-api.alpaca.markets', api_version='v2')
clock = api.get_clock()

market_open_flag = False


def get_ip():
    ip = requests.get('https://api.ipify.org').text
    print(f"PUBLIC IP: {ip}")


def record_intraday(conn, table_name, symbol, interval):
    intraday_list = []

    while True:
        now = dt.datetime.now()
        current_price = requests.get(f"https://financialmodelingprep.com/api/v3/quote-short/{symbol}?apikey=992f4ace89c00105ff6c15b225372d70")
        current_price = current_price.json()

        for value in current_price:
            print(value)
            intraday_list.append([f"{now.hour}:{now.minute}:{now.second}", value['symbol'], value['price'], value['volume']])
            # ROW COLUMNS: (TIME, SYMBOL, PRICE, VOLUME, ID)
            msql.insert_values(conn, table_name, 'time, symbol, price, volume', f"'{now.hour}:{now.minute}:{now.second}', '{value['symbol']}', '{value['price']}', '{value['volume']}'")

            #FOR OUTPUT MONITORING ONLY
            print(f"{msql.get_last(conn, table_name)}")

        if now.hour >= 15 and now.minute >= 30:
            msql.close_connection(conn)
            market_open_flag = False
            break

        time.sleep(interval)

    intraday_df = pd.DataFrame(intraday_list, columns=['TIME', "SYMBOL", 'PRICE', 'VOLUME'])
    intraday_df.to_excel(f'{now.strftime("%Y%m%d%H%m")}_{symbol}_output.xlsx', sheet_name=f'{now.strftime("%Y%m%d%H%m")}_{symbol}_intraday')

    msql.close_connection(conn)
    print(intraday_df)


def main(symbol, table_name):

    conn = msql.mysql_connect()
    with conn:
        msql.table_exists(conn, table_name)
        if msql.table_exists(conn, table_name):
            print(f"{table_name} exists...skipping")
            return None
        else:
            # print(f"{table_name} does not exist...continuing")
            current_price = requests.get(
                f"https://financialmodelingprep.com/api/v3/quote-short/{symbol}?apikey=992f4ace89c00105ff6c15b225372d70")
            current_price = current_price.json()

            for row in current_price:
                if not 'price' in row:
                    # print(f"{row} does not contain price")
                    return None
                else:
                    # print(f"{row} contains price")
                    msql.create_table(conn, table_name)
                    msql.purge_table(conn, table_name)
                    record_intraday(conn, table_name, symbol, 30)
                    return None


if __name__ == "__main__":
    # # GET ARGS
    # parser = argparse.ArgumentParser(description="Select Stock Symbol")
    # parser.add_argument('--symbol', metavar='symbol', type=str, help='NYSE Stock Symbol')
    #
    # args = parser.parse_args()
    # symbol = args.symbol
    #
    # if symbol is None:
    #     print(f"USER INPUT VALIDATION FAILED!\nPlease enter a symbol identifier...")
    #     sys.exit()
    # else:
    #     print(f"USER SYMBOL INPUT: {symbol}")

    # interval is in seconds..eg: 60 = 60seconds(1min)

    after_close_flag = False
    before_open_flag = False

    while not market_open_flag:
        now = dt.datetime.now()


        if now.hour <= 8 and now.minute < 30:
            before_open_flag = True

        if now.hour >= 15 and now.minute > 30:
            after_close_flag = True

        if now.hour >= 8 and now.minute >= 30 or clock.is_open:
            print(f"Market is open...recording data!\n")
            get_ip()
            market_open_flag = True
            break
        elif not clock.is_open or before_open_flag or after_close_flag:
            if name == 'nt':
                system("cls")
            else:
                system("clear")
            print(f"Market is not open...sleeping for 60 seconds")
            time.sleep(30)

    if market_open_flag:
        nyse_data = pd.read_excel('NYSE.xlsx')
        nyse_df = pd.DataFrame(nyse_data)

        now1 = dt.datetime.now()

        start = time.time()
        for index, row in nyse_df.iterrows():
            if '-' in row[0]:
                continue
            elif '.' in row[0]:
                continue
            elif '^' in row[0]:
                continue
            else:
                # Check if table exists (which indicates a recorder is already running)
                # if table exists skip to next symbol
                symbol = row[0]

                table_name = f'{now1.strftime("%Y%m%d")}_{symbol}_data'
                # print(f"TABLE NAME:\n{table_name}")
                main(symbol, table_name)
        end = time.time()
        time_elapsed = round((end - start) / 2, 2)
        print(f"Time Elapsed: {time_elapsed}")

        # now1 = dt.datetime.now()
        # table_name = f'{now1.strftime("%Y%m%d")}_{symbol}_data'
        # print(f"TABLE NAME:\n{table_name}")
        # main(symbol, table_name)
