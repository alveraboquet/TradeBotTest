import alpaca_trade_api as tradeapi
import pandas as pd
import time
import argparse
import sys
import datetime as dt
import pickle
import concurrent.futures
import __math_functions as mf
import __broker_functions as bf

api = tradeapi.REST('PKI9T8QMB3XFEB8IKY95', 'KzrlaRVyafuctfWqQ67jb4Q6CCrMhSumHfPPwITO', 'https://paper-api.alpaca.markets', api_version='v2')

market_open_flag = False

top10 = [[]]
sell_list = [[]]

symbol_list = []


def main(vars_dict):
    #restart after sleeping
    print("Finished...sleeping for 30 seconds then restarting!")
    time.sleep(5)

    nasdaq_data = pd.read_excel("./INPUT/NASDAQ_1.xlsx")
    nasdaq_df = pd.DataFrame(nasdaq_data)\

    row_last = 0
    for index, row in nasdaq_df.iterrows():
        symbol = str(row[0])
        # sanitize input
        if '-' in symbol:
            continue
        elif '.' in symbol:
            continue
        elif '^' in symbol:
            continue
        elif '/' in symbol:
            continue
        elif '=' in symbol:
            continue
        elif '+' in symbol:
            continue
        elif len(symbol) > 4:
            continue
        elif row_last == symbol:
            continue
        else:
            symbol_list.append(symbol)
            row_last = symbol

    start = time.time()
    NUMBER_THREADS = min(30, len(symbol_list))
    print(NUMBER_THREADS)

    with concurrent.futures.ThreadPoolExecutor(max_workers=NUMBER_THREADS) as executor:
        results = executor.map(mf.get_movingavg, symbol_list)
        # results = executor.map(mf.get_ema, symbol_list)
        for result in results:
            if not result == None:
                print(result)

    end = time.time()
    time_elapsed = round((end - start), 2)
    if time_elapsed > 60:
        time_elapsed = round(time_elapsed / 60, 2)
        print(f"Time Elapsed: {time_elapsed} minutes")
    else:
        print(f"Time Elapsed: {time_elapsed} seconds")

    mf.get_position_list()
    mf.get_variation() # ONLY FOR SMA


if __name__ == "__main__":
    vars_filename = 'tradebot_vars'
    outfile = open(vars_filename, 'w+b')

    # INIT DEFAULTS
    vars_dict = {'buy_counter': 0, 'sell_counter': 0, 'progression_counter': 0, 'regression_counter': 0,
                 'stoploss_price': 0, 'buy_flag': False, 'sell_flag': False, 'progression_flag': False,
                 'regression_flag': False,
                 'is_owned': False, 'account_value': 100000, 'yearly_return': 0, 'order_id': 0}

    pickle.dump(vars_dict, outfile)
    outfile.close()

    infile = open(vars_filename, 'rb')

    vars_dict = pickle.load(infile)

    account_value = vars_dict['account_value']

    # interval is in seconds..eg: 60 = 60seconds(1min)

    after_close_flag = False
    before_open_flag = False

    while not market_open_flag:
        now = dt.datetime.now()
        break


        if now.hour <= 8 and now.minute < 30:
            before_open_flag = True

        if now.hour >= 15:
            after_close_flag = True

        if now.hour >= 8 and now.minute >= 30 or bf.is_open():
            print(f"Market is open...recording data!\n")
            market_open_flag = True
            break
        elif not clock.is_open or before_open_flag or after_close_flag:
            if name == 'nt':
                system("cls")
            else:
                system("clear")
            print(f"Market is not open...sleeping for 60 seconds")
            time.sleep(30)

    if not market_open_flag:
        main(vars_dict)
