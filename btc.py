import pandas as pd
import pickle
import __mysql as mysql
import datetime as dt
import requests
import urllib3
import time
from time import sleep
import simplejson
from logger import write_log
import ftx
import math

price_list = []

## FTX KEYS ##
API_KEY = 'Ueu9-JXo6pjUilfQBXXKUBCBTPRPGGtmH_sJzCly'
API_SECRET = 'pXTq_BCTKHeV_m4T6FCkrrFZqIdsE3wrJgfCLRZx'

client = ftx.FtxClient(api_key=API_KEY, api_secret=API_SECRET)


def apply_fee(price):
    price_fee = round(price * .0007, 4)
    price = round(price + price_fee, 4)

    print('\nFEE CALCULATED: ' + str(price_fee) + '\n')

    return price


def calculate_fee(price):
    price_fee = round(price * .0007, 4)

    return price_fee


def calculate_qty(ask, price):
    qty = round(ask / price, 6)

    return qty


def btc_sma(conn, vars_dict, table):
    try:
        price = client.get_market('BTC/USD')['price']

        price_log(conn, 'price_log', price)

        if price == vars_dict['last_price']:
            return None
    except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError, urllib3.exceptions.NewConnectionError,
            urllib3.exceptions.MaxRetryError, simplejson.errors.JSONDecodeError, requests.exceptions.HTTPError, Exception) as e:
        write_log(f"ERROR HAS OCCURRED!")
        write_log(e)
        print(f"\nRead timeout occurred...sleeping for 30 seconds then retrying!")
        print(f"{e}")
        sleep(30)
        return None

    if price == vars_dict['last_price']:
        return None

    price_list.append(price)

    df = pd.DataFrame(price_list)

    df_ema = df.ewm(span=30, adjust=False).mean()
    current_ema = float(df_ema.iloc[-1][0])
    current_ema = round(current_ema, 4)

    df_sma = df.rolling(51).mean()
    current_sma = float(df_sma.iloc[-1][0])
    current_sma = round(current_sma, 4)

    profit = (price * vars_dict['qty_owned']) - vars_dict['last_transaction']
    ema_var = price - current_ema

    now = dt.datetime.now()
    time_now = f"{now.hour}:{now.minute}:{now.second}"

    if price > current_sma and not vars_dict['is_owned']:
        # shows progressive action...calculate interior angle to determine position
        print(f"\nDEBUG: PRICE: {price} | EMA: {current_ema} | SMA: {current_sma}")
        vars_dict['progression_counter'] = 0
        vars_dict['regression_counter'] = 0
        ask = vars_dict['account_value'] * .8
        qty = calculate_qty(ask, price)
        fee = calculate_fee(ask)
        total = (price * qty) + fee
        print(f"Buying {qty} of BTC for a price of {price * qty} + fee of {fee} for a total of {total}")

        vars_dict['is_owned'] = True
        vars_dict['defaulted'] = False
        vars_dict['account_value'] -= price * qty
        vars_dict['last_transaction'] = ask + fee
        vars_dict['qty_owned'] = qty

        print(f"\nACCOUNT VALUE: {vars_dict['account_value']}\n")

        # UPDATE TABLES
        if math.isnan(current_sma):
            current_sma = 0

        mysql.insert_values(conn, table, 'datetime, position, price, ask, qty, ema, sma, profit, fee, account_value',
                            f"'{time_now}', 'BUY', '{price}', '{ask}', '{qty}', '{current_ema}', '{current_sma}', "
                            f"'{profit}', '{fee}', '{vars_dict['account_value']}'")

    if vars_dict['is_owned'] and price < current_sma:
        print(f"\nDEBUG: PRICE: {price} | EMA: {current_ema} | SMA: {current_sma}")
        vars_dict['progression_counter'] = 0
        vars_dict['regression_counter'] = 0
        qty = vars_dict['qty_owned']
        ask = price * qty
        fee = calculate_fee(ask)
        print(f"Selling {qty} of BTC for a price of {price * qty} + fee of {fee} for a total profit of {profit}")

        vars_dict['is_owned'] = False
        vars_dict['account_value'] += price * qty
        vars_dict['last_transaction'] = 0
        vars_dict['qty_owned'] = 0

        print(f"\nACCOUNT VALUE: {vars_dict['account_value']}\n")

        # UPDATE TABLES
        if math.isnan(current_sma):
            current_sma = 0

        mysql.insert_values(conn, table, 'datetime, position, price, ask, qty, ema, sma, profit, fee, account_value',
                            f"'{time_now}', 'SELL', '{price}', '{ask}', '{qty}', '{current_ema}', '{current_sma}', "
                            f"'{profit}', '{fee}', '{vars_dict['account_value']}'")

    if vars_dict['is_owned']:
        print(f"\rPROFIT: {profit} | PRICE: {price} | EMA: {current_ema} | VAR: {price - current_ema} | PRO: {vars_dict['progression_counter']} | REG: {vars_dict['regression_counter']}")
        vars_dict['last_profit'] = profit

    vars_dict['last_price'] = price


def price_log(conn, table, price):
    now = dt.datetime.now()
    time_now = f"{now.hour}:{now.minute}:{now.second}"

    # UPDATE TABLES
    mysql.insert_values(conn, table, 'datetime, price',
                        f"'{time_now}', '{price}'")


def check_ip():
    ip = requests.get('https://api.ipify.org').text
    write_log(f"PUBLIC IP ADDRESS: {ip}")
    print(f"\nPUBLIC IP ADDRESS: {ip}\n")


def get_defaults(conn, vars_dict):
    # GET ACCOUNT VALUE FROM SQL DATABASE THEN ASSIGN THAT TO PICKLE
    vars_dict['account_value'] = mysql.get_account_value(conn)

    if vars_dict['account_value'] == None:
        print(f"Received NULL account value...setting static value of 1000")
        vars_dict['account_value'] = 1000

    try:
        if mysql.get_last_position(conn, 'trade_log')[2] == 'BUY':
            # print(mysql.get_last_position(conn, 'trade_log'))
            vars_dict['is_owned'] = True
            vars_dict['last_transaction'] = (
                        mysql.get_last_position(conn, 'trade_log')[4] + mysql.get_last_position(conn, 'trade_log')[9])
            vars_dict['qty_owned'] = mysql.get_last_position(conn, 'trade_log')[5]
            vars_dict['last_price'] = mysql.get_last_position(conn, 'trade_log')[3]
            vars_dict['ema'] = mysql.get_last_position(conn, 'trade_log')[6]
            vars_dict['defaulted'] = True

            print(f"\nSET DEFAULTS:")
            print(
                f"ACCOUNT VALUE: {vars_dict['account_value']} | IS_OWNED: {vars_dict['is_owned']} | LAST_TRANSACTION: "
                f"{vars_dict['last_transaction']} | QTY_OWNED: {vars_dict['qty_owned']} | "
                f"LAST_PRICE: {vars_dict['last_price']} | EMA: {vars_dict['ema']} | DEFAULTED: {vars_dict['defaulted']}\n")
    except TypeError as e:
        print(f"Table is empty...proceeding!")

    return vars_dict


def main(vars_dict):
    print('main')

    check_ip()

    sql_url = 'mysql+pymysql://root:drnm9qr7@34.66.220.115/trades'

    try:
        conn = mysql.mysql_connect(sql_url)
    except UnboundLocalError as e:
        write_log(e)
        print(e)
        return None

    with conn:
        if mysql.table_exists(conn, 'trade_log'):
            print("Table exist...proceeding!")

            # GET DEFAULTS
            vars_dict = get_defaults(conn, vars_dict)

            print(f"\nACCOUNT VALUE: {vars_dict['account_value']}")

            while True:
                btc_sma(conn, vars_dict, 'trade_log')

                time.sleep(5)
        else:
            print("Table doesnt exist!")


if __name__ == "__main__":
    vars_filename = 'btc_vars'
    outfile = open(vars_filename, 'w+b')

    # INIT DEFAULTS
    vars_dict = {'buy_counter': 0, 'sell_counter': 0, 'progression_counter': 0, 'regression_counter': 0,
                 'stoploss_price': 0, 'buy_flag': False, 'sell_flag': False, 'progression_flag': False,
                 'regression_flag': False,
                 'is_owned': False, 'account_value': 500, 'last_transaction': 0, 'transaction_profit': 0, 'last_price': 0,
                 'last_var': 0, 'profit_progression': 0, 'profit_regression': 0, 'last_profit': 0, 'profit_var': 0,
                 'profit_var_last': 0, 'qty_owned': 0, 'ema': 0, 'defaulted': False}

    pickle.dump(vars_dict, outfile)
    outfile.close()

    infile = open(vars_filename, 'rb')

    vars_dict = pickle.load(infile)

    main(vars_dict)