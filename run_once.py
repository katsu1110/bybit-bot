import json
import time
import datetime
import requests
import pybybit
import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression, Ridge
import importlib

from config import get_config
from logic_funcs import feature_engineering, get_model, logic
from data_get_funcs import get_btc_ohlcv, get_depth, get_data
from bybit_funcs import get_position, market_order, limit_order, limit_multi_order
from utils import discord_Notify

config = get_config()
discord_url = config['discord_url']
apis = [
    config['api'],
    config['secret']
]
bybit = pybybit.API(*apis, testnet=config['testnet'])
discord_Notify(f"start!!! {datetime.datetime.now()}")


# time.sleep(5)
# flg = 0
# while True:
#     print("check!!!")
#     try:
#         pos = get_position(bybit, config['margin_rate'])
#         print("success!!!")
#         flg = 1
#     except:
#         print("fail!!!")
#         time.sleep(5)
#     if flg == 1:
#         break

#next_time = np.inf
next_time = int(datetime.datetime.now().timestamp()) // 86400 * 86400 + 86400 + 300
#next_time = int(datetime.datetime.now().timestamp()) + 10
message = f"Next Time is : {datetime.datetime.fromtimestamp(next_time)}"
discord_Notify(message)


if True:
#    importlib.reload(config)
    config = get_config()
    now_time = int(datetime.datetime.now().timestamp())
#    if now_time > next_time:
    if True:
        print("bidding!!!")
#        next_time = int(datetime.datetime.now().timestamp()) // 86400 * 86400 + 86400 + 300
#         next_time = int(datetime.datetime.now().timestamp()) // 8 * 8 + 8
#        message = f"Next Time is : {datetime.datetime.fromtimestamp(next_time)}"
#        discord_Notify(message)
        side, size = get_position(bybit)
        pred = logic()
        if pred > 0:
            ## Buy
            if side != 'Buy':
#                 message = limit_order(bybit, 'Buy', pos[2])
                message = limit_multi_order(bybit, 'Buy', size, config["qty"])
            else:
                message = 'No change. Side:' + str(side) + ' lot:' + str(size)
                discord_Notify(message)
        else:
            ## Sell
            if side != 'Sell':
#                 message = limit_order(bybit, 'Sell', pos[2])
                message = limit_multi_order(bybit, 'Sell', size, config["qty"])
            else:
                message = 'No change. Side:' + str(side) + ' lot:' + str(size)
                discord_Notify(message)
#        print(message)
#    else:
#        time.sleep(10)

