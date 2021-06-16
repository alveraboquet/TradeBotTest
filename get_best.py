import alpaca_trade_api as tradeapi
import pandas as pd
import datetime
import time
import concurrent.futures
import __math_functions as mf
import __broker_functions as bf


api = tradeapi.REST('PKI9T8QMB3XFEB8IKY95', 'KzrlaRVyafuctfWqQ67jb4Q6CCrMhSumHfPPwITO', 'https://paper-api.alpaca.markets', api_version='v2')
top10 = [[]]
sell_list = [[]]
sell_mode = False

symbol_list = []


def get_top_ten():
    now1 = datetime.datetime.now()
    datalist = pd.read_excel(f'{now1.strftime("%Y%m%d%H%m")}_output.xlsx', index_col=0)
    datalist_df = pd.DataFrame(datalist, columns=[0, 1])
    datalist_df.sort_values(by=1, inplace=True, ascending=False)
    datalist_df = datalist_df[:10]
    datalist_df = datalist_df.reset_index(drop=True)

    datalist_df.to_excel(f'{now1.strftime("%Y%m%d%H%m")}_cleaned.xlsx')
    for index, row in datalist_df.iterrows():
        bf.buy_order(row[0], 100)


account = api.get_account()
portfolio = api.list_positions()
clock = api.get_clock()
# stocklist_temp = ['AAPL', 'AMD', 'PFE', 'SWBI', 'VSTO', 'INTC', 'RGR', 'OLN', 'RHE', 'HOME']
stocklist_data = pd.read_excel('NYSE_ORIGIN_ALL.xlsx')
stocklist_df = pd.DataFrame(stocklist_data)
print('[+] ACCOUNT NUMBER: ' + account.account_number)
print('[+] ACCOUNT CASH: ' + account.cash)
print('[+] PORTFOLIO VALUE: ' + account.portfolio_value + '\n')
for positions in portfolio:
    print(f'[+] OPEN POSITION: {positions.qty} {positions.symbol}')
# STEP 1
# LOOP THROUGH OPEN POSITIONS WITH ALGO AND IF REGRESSION EXISTS
# THEN CLOSE THOSE POSITIONS
# get_positions()
# close_positions()
# RESET top10 list for indexing in stocklist
top10 = [[]]
# STEP 2
# SCAN NYSE FOR POTENTIAL BUY CANDIDATES WITH ALGO
# start = time.time()
for index, row in stocklist_df.iterrows():
    if '-' in row[0]:
        continue
    elif '.' in row[0]:
        continue
    elif '^' in row[0]:
        continue
    elif len(row[0]) > 4:
        continue
    else:
        symbol = row[0]
        symbol_list.append(symbol)

# end = time.time()
# time_elapsed = round((end - start) / 2, 2)
# time_in_mins = time_elapsed / 60
# print(f"Time Elapsed: {time_in_mins}")
# print(len(symbol_list))

start = time.time()
NUMBER_THREADS = min(30, len(symbol_list))
print(NUMBER_THREADS)

with concurrent.futures.ThreadPoolExecutor(max_workers=NUMBER_THREADS) as executor:
    results = executor.map(get_ema, symbol_list)
    for result in results:
        if not result == None:
            print(result)

end = time.time()
time_elapsed = round((end - start), 2)
print(f"Time Elapsed: {time_elapsed}")

# STEP 3
# OUTPUT STEP 2 TO EXCEL SHEET FOR CLEANING IN STEP 4
now = datetime.datetime.now()
top10_output = pd.DataFrame(top10)
top10_output.to_excel(f'{now.strftime("%Y%m%d%H%m")}_output.xlsx', sheet_name="Top10")

# STEP 4
# CLEAN OUTPUT FROM STEP 3 TO ONLY DISPLAY TOP 10 PERFORMING STOCKS
# AFTER LIST IS SORTED AND FORMATTED, BUY THE STOCKS, QTY = STATIC 100 FOR NOW
get_top_ten()