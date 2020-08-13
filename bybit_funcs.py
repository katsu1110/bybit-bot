import json
import time
import datetime
import requests
import pybybit
import numpy as np
import pandas as pd
from config import get_config
from sklearn.linear_model import LinearRegression, Ridge

from utils import discord_Notify

def get_position(bybit, margin_rate):
    while True:
        try:
            pos = bybit.rest.inverse.private_position_list(symbol='BTCUSD')
            pos = pos.json()['result']
            pos['side']
            break
        except Exception as e:
            message = 'Get pos failed.:' + str(e)
            discord_Notify(message)
            time.sleep(2)
            continue
    while True:
        try:
            tic = bybit.rest.inverse.public_tickers(symbol='BTCUSD')
            tic = tic.json()['result'][0]
            break
        except Exception as e:
            message = 'Get tic failed.:' + str(e)
            discord_Notify(message)
            time.sleep(2)
            continue
    side = str(pos['side'])
    size = int(pos['size'])
    price = float(tic['mark_price'])
    wallet_balance = float(pos['wallet_balance'])
    leverage = int(pos['leverage'])
    order_lot = int(price * wallet_balance * leverage * margin_rate + size)
    return [side, size, order_lot]

def market_order(bybit, side, order_lot):
    while True:
        try:
            res = bybit.rest.inverse.private_order_create(side=side, symbol='BTCUSD', order_type='Market', qty=order_lot, time_in_force='GoodTillCancel')
            res = res.json()
            break
        except Exception:
            message = side + ' order failed.'
            discord_Notify(message)
            time.sleep(5)
            continue
    if res['ret_msg'] != 'OK':
        message = side + ' order failed. msg:' + res['ret_msg']
        discord_Notify(message)
    else:
        message = side + ' order completed. order_lot:' + str(order_lot)
        discord_Notify(message)
    return message


def limit_order(bybit, side, order_lot):
    while True:
        try:
            bybit.rest.inverse.private_order_cancelall("BTCUSD")
            tic = bybit.rest.inverse.public_tickers("BTCUSD")
            tic = tic.json()['result']
            price = tic[0]["last_price"]
            res = bybit.rest.inverse.private_order_create(side=side, symbol='BTCUSD', price = price,
                                                          order_type='Limit', qty=order_lot, time_in_force='GoodTillCancel')
            res = res.json()
            break
        except Exception:
            message = side + ' order failed.'
            discord_Notify(message)
            time.sleep(5)
            continue
    if res['ret_msg'] != 'OK':
        message = side + ' order failed. msg:' + res['ret_msg']
        discord_Notify(message)
    else:
        message = side + ' order completed. order_lot:' + str(order_lot)
        discord_Notify(message)
    return message