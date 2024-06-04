#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 24 13:50:04 2024

@author: akshathaaavinashannadhani
"""

import datetime
import pandas as pd
import sqlite3
from dateutil.relativedelta import relativedelta


# Use this function for SQLITE3
def connect_db():
    conn = sqlite3.connect("expense.db")
    cur = conn.cursor()
    cur.execute(
        '''CREATE TABLE IF NOT EXISTS user_login (user_id INTEGER PRIMARY KEY AUTOINCREMENT, username VARCHAR(30) NOT NULL, 
        email VARCHAR(30) NOT NULL UNIQUE, password VARCHAR(20) NOT NULL)''')
    cur.execute(
        '''CREATE TABLE IF NOT EXISTS user_expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, pdate DATE NOT 
        NULL, expense VARCHAR(10) NOT NULL, amount INTEGER NOT NULL, pdescription VARCHAR(50), FOREIGN KEY (user_id) 
        REFERENCES user_login(user_id))''')
    conn.commit()
    return conn, cur


def close_db(connection=None, cursor=None):
    """
    close database connection
    :param connection:
    :param cursor:
    :return: close connection
    """
    cursor.close()
    connection.close()


def execute_query(operation=None, query=None):
    """
    Execute Query
    :param operation:
    :param query:
    :return: data in case of search query or write to database
    """
    connection, cursor = connect_db()
    if operation == 'search':
        cursor.execute(query)
        data = cursor.fetchall()
        cursor.close()
        return data
    elif operation in ['insert', 'delete']:
        cursor.execute(query)
        connection.commit()
        cursor.close()
        connection.close()
        return None


def generate_df(df):
    """
    create new features
    :param df:
    :return: df
    """
    df = df
    df['Date'] = pd.to_datetime(df['Date'])
    df['Year'] = df['Date'].dt.year
    df['Month_name'] = df['Date'].dt.month_name()
    df['Month'] = df['Date'].dt.month
    df['Day_name'] = df['Date'].dt.day_name()
    df['Day'] = df['Date'].dt.day
    df['Week'] = df['Date'].dt.isocalendar().week
    return df


def num2MB(num):
    """
        num: int, float
        it will return values like thousands(10K), Millions(10M),Billions(1B)
    """
    if num < 1000:
        return int(num)
    if 1000 <= num < 1000000:
        return f'{float("%.2f" % (num / 1000))}K'
    elif 1000000 <= num < 1000000000:
        return f'{float("%.2f" % (num / 1000000))}M'
    else:
        return f'{float("%.2f" % (num / 1000000000))}B'


def top_tiles(df=None):
    """
    Sum of total expenses
    :param df:
    :return: sum
    """
    if df is not None:
        tiles_data = df[['Expense', 'Amount']].groupby('Expense').sum()
        tiles = {'Earning': 0, 'Investment': 0, 'Saving': 0, 'Spend': 0}
        for i in list(tiles_data.index):
            try:
                tiles[i] = num2MB(tiles_data.loc[i][0])
            except:
                pass
        return tiles['Earning'], tiles['Spend'], tiles['Investment'], tiles['Saving']
    return


def get_monthly_spendings_and_savings(df, budget):
    """
    Retrieve monthly spendings, savings, and budget for the previous num_months months.

    :param df: Pandas DataFrame containing expense data
    :param budget: User's budget for the month
    :return: A dictionary with monthly spendings, savings, and budget
    """
    monthly_data = {}
    for i in range(3):
        month = datetime.date.today().replace(day=1) - relativedelta(months=i)
        month_name = month.strftime("%B")
        month_spendings = df[(df['Date'].dt.year == month.year) & (df['Date'].dt.month == month.month) & (df['Expense'] == 'Spend')]['Amount'].sum()
        month_savings = df[(df['Date'].dt.year == month.year) & (df['Date'].dt.month == month.month) & (df['Expense'] == 'Saving')]['Amount'].sum()
        monthly_data[month_name] = {'Spendings': num2MB(month_spendings), 'Savings': num2MB(month_savings), 'Budget': budget}
    return monthly_data