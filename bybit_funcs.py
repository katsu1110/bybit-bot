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
from pred_funcs import pred_logic
from config import get_config


def limit_order_perf(bybit, pred, margin_rate):
    delta = 0.5
    while True:
        time.sleep(60)
        side, size, order_lot = get_position(bybit, margin_rate)
        bybit.rest.inverse.private_order_cancelall("BTCUSD") ## cancel
        if pred > 0:
            ## Buy
            if side != 'Buy':
                message = limit_order(bybit, 'Buy', order_lot, delta = delta)
            else:
                message = 'No change. Side:' + str(side) + ' lot:' + str(size)
                discord_Notify(message)
                break
        else:
            ## Sell
            if side != 'Sell':
                message = limit_order(bybit, 'Sell', order_lot, delta = delta)
            else:
                message = 'No change. Side:' + str(side) + ' lot:' + str(size)
                discord_Notify(message)
                break
        discord_Notify(message)
    

def get_position(bybit, margin_rate):
    while True:
        try:
            pos = bybit.rest.inverse.private_position_list(symbol='BTCUSD')
            pos = pos.json()['result']
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
    return side, size, order_lot


def market_order(bybit, side, order_lot):
    while True:
        try:
            res = bybit.rest.inverse.private_order_create(side=side, symbol='BTCUSD', order_type='Market', qty=order_lot, time_in_force='GoodTillCancel')
            res = res.json()
            break
        except Exception as e:
            print(e)
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


def limit_order(bybit, side, order_lot, delta = 5):
    while True:
        try:
            if side == "Sell":
                coef = 1
            if side == "Buy":
                coef = -1
#            bybit.rest.inverse.private_order_cancelall("BTCUSD")
            tic = bybit.rest.inverse.public_tickers("BTCUSD")
            tic = tic.json()['result']
            price = float(tic[0]["last_price"])
            res = bybit.rest.inverse.private_order_create(side=side, symbol='BTCUSD', price = str(price + delta * coef),
                                                          order_type='Limit', qty=str(order_lot), time_in_force='PostOnly')
            res = res.json()
            break
        except Exception as e:
            print(e)
            message = side + ' order failed.'
            discord_Notify(message)
            time.sleep(5)
            continue
    if res['ret_msg'] != 'OK':
        message = side + ' order failed. msg:' + res['ret_msg']
    else:
        message = side + ' order completed. order_lot:' + str(order_lot) + " price: " + str(price)
    return message



def limit_multi_order(bybit, side, now_size, order_lot):
    while True:
        try:
#            bybit.rest.inverse.private_order_cancelall("BTCUSD")
            
#             deltas = [5] + [delta * 2 ** (k) for k in range(num)]
            deltas = [5, 100, 250]
            if side == "Sell":
                coef = 1
            if side == "Buy":
                coef = -1
            print(deltas)
            for i, delta in enumerate(deltas):
                tic = bybit.rest.inverse.public_tickers("BTCUSD")
                tic = tic.json()['result']
                price = float(tic[0]["last_price"])
                if i == 0:
                    lot = now_size + order_lot
                else:
                    lot = order_lot
                print(delta, price, lot, side)
                res = bybit.rest.inverse.private_order_create(side=side, symbol='BTCUSD', price = str(price + delta * coef),
                                                      order_type='Limit', qty=str(lot), time_in_force='GoodTillCancel')
                res = res.json()
                time.sleep(5)
            break
        except Exception as e:
            print(e)
            message = side + ' order failed.'
            discord_Notify(message)
            time.sleep(5)
            continue
    if res['ret_msg'] != 'OK':
        message = side + ' order failed. msg:' + res['ret_msg']
        discord_Notify(message)
    else:
        message = side + ' order completed. order_lot:' + str(order_lot) + " price: " + str(price)
        discord_Notify(message)
    return message


if __name__ == "__main__":
    config = get_config()
    apis = [
        config['api'],
        config['secret']
    ]
    bybit = pybybit.API(*apis, testnet=config['testnet'])
    print("position...")    
    print(get_position(bybit, config["margin_rate"]))
    print("limit order perf...")    
    config["margin_rate"] = 0.001
    print("pred...")
    pred = 0.8#pred_logic()
    print("order...")
    limit_order_perf(bybit, pred, config["margin_rate"])
