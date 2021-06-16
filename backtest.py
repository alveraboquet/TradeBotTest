import pandas as pd
import pickle
import numpy as np
import requests
import math
import matplotlib.pyplot as plot
import yahoo_fin.stock_info as si

position_list = []
profit_list = []

var_last = 0

progression_counter = 0
regression_counter = 0
progression_flag = False
regression_flag = False


def record_position(date, position, price, account_value):
    position_list.append([date, position, price, account_value])

def write_pickle(dict):
    filename = "backtest_vars"
    outfile = open(filename, 'w+b')

    pickle.dump(dict, outfile)
    outfile.close()


def backtest_daily(vars_dict, date, close, sma5, sma30, var_this, var_last):
    # print(f"**Var This: {var_this} | Var Last: {var_last}")

    if close <= vars_dict['stoploss_price'] and vars_dict['is_owned']:
        if 'STOPLOSS' in position_list[-1][1]:
            return var_this
        else:
            vars_dict['account_value'] = vars_dict['account_value'] + (close * 1000) # TODO: UPDATE THIS TO DYNAMICALLY ALLOCATE NUMBER OF SHARES TO BUY/SELL
            record_position(date, 'STOPLOSS', close, vars_dict['account_value'])

            vars_dict['buy_flag'] = False
            vars_dict['sell_flag'] = False
            vars_dict['buy_counter'] = 0
            vars_dict['sell_counter'] = 0
            # vars_dict['progression_flag'] = False
            # vars_dict['regression_flag'] = False
            # vars_dict['progression_counter'] = 0
            # vars_dict['regression_counter'] = 0
            vars_dict['is_owned'] = False
            vars_dict['stoploss_price'] = 0

            return var_this

    # BUY - SHORT > LONG && !IS_OWNED
    if sma5 > sma30 and not vars_dict['is_owned']:
        # print(date, close, sma5, sma30, var_this)
        vars_dict['buy_counter'] += 1

        if var_this > var_last:
            vars_dict['progression_counter'] += 1
            var_last = var_this
        elif var_this < var_last:
            vars_dict['regression_counter'] += 1
            var_last = var_this
        else:
            var_last = var_this

        if vars_dict['progression_counter'] >= 1 and not vars_dict['is_owned']:
            # IF TREND IS POSITIVE AND WE DONT OWN...SEND BUY SIGNAL
            vars_dict['progression_flag'] = True
            vars_dict['buy_flag'] = True
            vars_dict['is_owned'] = True

            # RESET REGRESSION FLAGS - COUNTERS
            vars_dict['regression_flag'] = False
            vars_dict['regression_counter'] = 0

            # UPDATE ACCOUNT VALUES
            vars_dict['account_value'] =  vars_dict['account_value'] - (close * 1000) # TODO: UPDATE THIS TO DYNAMICALLY ALLOCATE NUMBER OF SHARES TO BUY/SELL
            vars_dict['stoploss_price'] = abs((close * .1) - close)
            record_position(date, 'BUY', close, vars_dict['account_value'])

            print(f"{date} is indicating PROGRESSION")


    # SELL - SHORT < LONG && IS_OWNED
    if sma5 < sma30 and vars_dict['is_owned']:
        vars_dict['sell_counter'] += 1

        if var_this > var_last:
            vars_dict['progression_counter'] += 1
            var_last = var_this
        elif var_this < var_last:
            vars_dict['regression_counter'] += 1
            var_last = var_this
        else:
            var_last = var_this

        if vars_dict['regression_counter'] >= 4 and vars_dict['is_owned']:
            # IF TREND IS NEGATIVE AND WE OWN...SEND SELL SIGNAL
            vars_dict['regression_flag'] = True
            vars_dict['sell_flag'] = True
            vars_dict['is_owned'] = False

            # RESET PROGRESSION FLAGS - COUNTERS
            vars_dict['progression_flag'] = False
            vars_dict['progression_counter'] = 0

            # UPDATE ACCOUNT VALUES
            vars_dict['account_value'] = vars_dict['account_value'] + (close * 1000) # TODO: UPDATE THIS TO DYNAMICALLY ALLOCATE NUMBER OF SHARES TO BUY/SELL
            vars_dict['stoploss_price'] = 0
            record_position(date, 'SELL', close, vars_dict['account_value'])

            print(f"{date} is indicating REGRESSION")

    write_pickle(vars_dict)

    return var_this


def backtest_intraday(values, period):
    print(values)
    # standard length = 21
    values = np.array(values)
    df_test = pd.DataFrame(values)
    df_test_ewma = df_test.ewm(span=period).mean()

    test = pd.DataFrame(df_test_ewma.tail(1))

    for index, row in test.iterrows():
        return round(row[0], 2)


vars_filename = 'backtest_vars'
outfile = open(vars_filename, 'w+b')

# INIT DEFAULTS
vars_dict = {'buy_counter': 0, 'sell_counter': 0, 'progression_counter': 0, 'regression_counter': 0,
             'stoploss_price': 0, 'buy_flag': False, 'sell_flag': False, 'progression_flag': False, 'regression_flag': False,
             'is_owned': False, 'account_value': 100000, 'yearly_return': 0, 'order_id': 0}

pickle.dump(vars_dict, outfile)
outfile.close()

infile = open(vars_filename, 'rb')

vars_dict = pickle.load(infile)

account_value = vars_dict['account_value']

# START INTRADAY BACKTEST

# df1_d = pd.read_excel(f"./INPUT/intraday_backtest_input_2.xlsx")
# df1 = pd.DataFrame(df1_d)
#
# price_list = []
#
# for index, row in df1.iterrows():
#     time = row[0]
#     price = row[2]
#     volume = row[3]
#
#     price_list.append(price)
#
#
# df_x = pd.DataFrame(price_list)
# df_x_ema = df_x.ewm(span=4).mean()
# df_x = df_x.append(df_x_ema)
# print(df_x)
# plot.plot(price_list)
# plot.show()

# END INTRADAY BACKTEST

# START DAILY BACKTEST

symbol = 'msft'
start_cash = 100000

stockprices = requests.get(f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?serietype=line&apikey=992f4ace89c00105ff6c15b225372d70")
stockprices = stockprices.json()
stockprices = stockprices['historical'][:14600] # 40 years

stockprices = pd.DataFrame.from_dict(stockprices)
stockprices = stockprices.set_index('date')

stockprices = stockprices.reindex(index=stockprices.index[::-1])

stockprices['SMA_5d'] = stockprices['close'].rolling(5).mean()
stockprices['SMA_30d'] = stockprices['close'].rolling(30).mean()
stockprices['SMA_VAR'] = stockprices['SMA_5d'] - stockprices['SMA_30d']

buy_counter = 0

for date, value in stockprices.iterrows():
    close = round(value[0], 2)
    sma5 = round(value[1], 2)
    sma30 = round(value[2], 2)

    if math.isnan(sma30):
        continue

    var_buffer = close/sma5
    variation = round((1 - var_buffer) * -1, 2)

    var_this = variation

    var_last = backtest_daily(vars_dict, date, close, sma5, sma30, var_this, var_last)

df1 = pd.DataFrame(position_list, columns=['DATE', 'POSITION', 'CLOSE_PRICE', 'ACCOUNT_VALUE'])
df1.to_excel(f'./outputs/{symbol}_position_list.xlsx')

if 'BUY' in position_list[-1][1]:
    curr_price = round(si.get_live_price(symbol), 2)
    vars_dict['account_value'] = vars_dict['account_value'] + (curr_price * 1000)

total_profit = float(vars_dict['account_value']) - start_cash
percent_growth = abs(round(((start_cash - vars_dict['account_value']) / start_cash * 100), 2))

print(f"\nSYMBOL: {symbol}")
print(f"\nSTARTING CASH: {start_cash}")
print(f"\nACCOUNT VALUE WITH ADJUSTMENT: {vars_dict['account_value']}")
print(f"\nTOTAL PROFIT: {total_profit}")
print(f"\nPERCENT GROWTH: {percent_growth}")

# END DAILY BACKTEST