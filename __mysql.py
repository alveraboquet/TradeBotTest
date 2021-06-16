import sqlalchemy
import pandas as pd
import os


def mysql_connect(url):
    # TODO: PARAMETERIZE THIS AND USE NON-ROOT LEVEL ACCESS
    db = sqlalchemy.create_engine(url)
    try:
        conn = db.connect()
    except Exception as e:
        print(f"CONNECT ERROR: \n{e}")

    return conn


def close_connection(conn):
    conn.close()

    print(f"Connection to DB closed!")


def create_table(conn, table_name):
    try:
        print(f"Creating table {table_name}...")
        sql = f"CREATE TABLE {table_name} (time TIME, symbol VARCHAR(4) NOT NULL, price FLOAT NOT NULL, volume INT, id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY)"
        query = sqlalchemy.text(sql)

        result = conn.execute(query)

    except Exception as e:
        print(f"ERROR creating table!\n{e}")


def list_all_records(conn, table):
    query = sqlalchemy.text(f"select * from {table}")

    result = conn.execute(query)

    for record in result:
        time = record[0]
        symbol = record[1]
        price = record[2]
        volume = record[3]
        id = record[4]

        print(f"Time: {time} | Symbol: {symbol} | Price: {price} | Volume:  {volume} | ID: {id}")


def list_columns(conn, table):
    sql = f"SELECT * FROM {table}"
    query = sqlalchemy.text(f"{sql}")

    result = conn.execute(query)

    for record in result:
        print(record)


def insert_values(conn, table, col, values):
    try:
        sql = f"INSERT INTO {table} ({col}) values ({values})"
        # print(sql)

        query = sqlalchemy.text(sql)

        result = conn.execute(query)

    except Exception as e:
        print(f"ERROR INSERTING VALUES:\n{e}")


def get_last(conn, table):
    try:
        sql = f"SELECT * FROM {table} WHERE id = (SELECT MAX(id) FROM {table})"
        query = sqlalchemy.text(sql)

        result = conn.execute(query)

        # print(f"LAST RECORD:")
        for record in result:
            return record[1]
            # print(
            #     f"Time: {record[0]} | Symbol: {record[1]} | Price: {record[2]} | Volume: {record[3]} | ID: {record[4]}")

    except Exception as e:
        print(f"Error getting last element:\n{e}")


def get_last_position(conn, table):
    try:
        sql = f"SELECT * FROM {table} WHERE id = (SELECT MAX(id) FROM {table})"
        query = sqlalchemy.text(sql)

        result = conn.execute(query)

        # print(f"LAST RECORD:")
        for record in result:
            # print(record[2])
            return record
    except Exception as e:
        print(f"Error getting last position:\n{e}")

def get_account_value(conn):
    try:
        sql = f"SELECT * FROM trade_log WHERE id = (SELECT MAX(id) FROM trade_log)"
        query = sqlalchemy.text(sql)

        result = conn.execute(query)

        for record in result:
            # print(f"{record[10]}")
            return record[10]
    except Exception as e:
        print(f"Error getting account info!")


def purge_table(conn, table):
    print(f"Purging {table}...")
    purge_query = f"DELETE FROM {table}"

    result = conn.execute(purge_query)


def table_exists(conn, table_name):
    try:
        sql = f"SHOW TABLES LIKE '{table_name}'"
        query = sqlalchemy.text(sql)

        result = conn.execute(query)

        table_list = [item[0] for item in result]
        if table_name in table_list:
            # print(table_list, " exists...appending to existing table!")
            return True
        else:
            # print(table_list, ' was not found...creating new table..')
            return False
    except Exception as e:
        print(f"Error getting table info!\n{e}")
