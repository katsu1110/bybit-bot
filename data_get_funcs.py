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


def get_btc_ohlcv():
    dfs = []
    for k in range(4):
        t = int((datetime.datetime.now() - datetime.timedelta(days = k * 365)).timestamp()) // 86400 * 86400
        f = int((datetime.datetime.now() - datetime.timedelta(days = (k + 1) * 365)).timestamp()) // 86400 * 86400    
        MEX_UDF_URL = 'https://www.bitmex.com/api/udf/history'
        mex_param = {
            'symbol':'XBTUSD',
            'resolution': '1D',
            'from':str(f),
            'to':str(t)
        }
        while True:
            try:
                res_mex = requests.get(MEX_UDF_URL, mex_param)
                res_mex.raise_for_status()
                break
            except Exception as e:
                message = 'Get xbt ohlcv failed.:' + str(e)
                discord_Notify(message)
                time.sleep(2)
                continue
        ohlcv = res_mex.json()
        data = pd.DataFrame(index=ohlcv['t'], columns=[])
        data['open'] = pd.DataFrame(ohlcv['o'], index=ohlcv['t'])
        data['high'] = pd.DataFrame(ohlcv['h'], index=ohlcv['t'])
        data['low'] = pd.DataFrame(ohlcv['l'], index=ohlcv['t'])
        data['close'] = pd.DataFrame(ohlcv['c'], index=ohlcv['t'])
        data['volume'] = pd.DataFrame(ohlcv['v'], index=ohlcv['t'])
        data = data.reset_index().rename(columns = {"index" : "time"})
        data["time"] = data["time"].apply(datetime.datetime.fromtimestamp)
        dfs.append(data)
#         data = data[:len(data)-1]
    data = pd.concat(dfs, axis = 0)
    data.rename
    data = data.sort_values(by = "time").reset_index(drop = True)
    data = data[:-1]
    return data

def get_depth():
    deps = []
    for i, bp in enumerate([5, 10, 20, 30, 50, 90]):
        dep_url = f'http://data.bitcoinity.org/export_data.csv?bp={bp}&bu=c&currency=USD&data_type=bidask_sum&exchange=bitmex&timespan=all'
        res_dep = requests.get(dep_url)

        with open('tmp.csv', 'wb') as f:
            f.write(res_dep.content)
        dep = pd.read_csv('tmp.csv')
        dep["time"] = dep["Time"].apply(lambda x : datetime.datetime.strptime(x[:-4], '%Y-%m-%d %H:%M:%S'))
        dep = dep.rename(columns = {"asks" : f"asks{bp}", "bids" : f"bids{bp}"})
        if i == 0:
            deps.append(dep)
        else:
            deps.append(dep.drop(["time", "Time"], axis = 1))

    dep = pd.concat(deps, axis = 1)
    return dep

def get_data():
    data = get_btc_ohlcv()
    dep = get_depth()
    df = data.merge(dep)
    df = df[["time", "close", "open", "high", "low", "volume",
    "asks5", "bids5", "asks10", "bids10", "asks20", "bids20", "asks30", "bids30", "asks50", "bids50", "asks90", "bids90"]]
    return df
