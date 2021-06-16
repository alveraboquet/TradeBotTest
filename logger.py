import datetime as dt
import os


def write_log(text):
    if not os.path.exists('log.txt'):
        f = open('log.txt', 'w')
        TIME_STAMP = dt.datetime.now()
        f.write(f"\n{TIME_STAMP} | {text}")
    else:
        f = open('log.txt', 'a')
        TIME_STAMP = dt.datetime.now()
        f.write(f"\n{TIME_STAMP} | {text}")

    f.close()