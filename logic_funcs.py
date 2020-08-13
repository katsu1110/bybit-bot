import json
import time
import datetime
import requests
import pybybit
import numpy as np
import pandas as pd
from config import get_config
from sklearn.linear_model import LinearRegression, Ridge

from data_get_funcs import get_data
from utils import discord_Notify

def feature_engineering(df):
#     df = pd.read_pickle("data.pkl")
    df["target"] = df["close"].diff().shift(-1)
    df["baseline"] = (df["close"] - df["open"]).shift(1) > 0
    
    df["feature_c-o"] = (df["close"] - df["open"])
    df["feature_h-c"] = (df["high"] - df["close"])
    df["feature_l-c"] = (df["low"] - df["close"])
    df["feature_h-o"] = (df["high"] - df["open"])
    df["feature_l-o"] = (df["low"] - df["open"])
    df["feature_h-l"] = (df["high"] - df["low"])

    feats = ["feature_c-o", "feature_h-c", "feature_l-c", "feature_h-o", "feature_l-o", "feature_h-l"]
    for shift in range(1, 3):
        for f in feats:
            df[f + f"_shift_{shift}"] = df[f].shift(shift)
    feats = [c for c in df.columns if "feature" in c]
    for f in feats:
        for rol in [7, 14]:
            df[f"{f}_vs_roll{rol}"] = df[f] > (df[f].rolling(rol).agg("mean"))
            
    df["feature_c-o_eth"] = (df["close_eth"] - df["open_eth"])
    df["feature_h-c_eth"] = (df["high_eth"] - df["close_eth"])
    df["feature_l-c_eth"] = (df["low_eth"] - df["close_eth"])
    df["feature_h-o_eth"] = (df["high_eth"] - df["open_eth"])
    df["feature_l-o_eth"] = (df["low_eth"] - df["open_eth"])
    df["feature_h-l_eth"] = (df["high_eth"] - df["low_eth"])

    feats = ["feature_c-o_eth", "feature_h-c_eth", "feature_l-c_eth", "feature_h-o_eth", "feature_l-o_eth", "feature_h-l_eth"]
    for f in feats:
        for rol in [7, 14]:
            df[f"{f}_vs_roll{rol}"] = df[f] > (df[f].rolling(rol).agg("mean"))
    for shift in range(1, 3):
        for f in feats:
            df[f + f"_shift_{shift}"] = df[f].shift(shift)
            
            
    for dep in [20, 30, 50, 90]:
        df[f"features_bid-ask{dep}"] = df[f"bids{dep}"] - df[f"asks{dep}"]
        for rol in [7, 14]:
            df[f"features_bid-ask{dep}_vs_roll{rol}"] = df[f"features_bid-ask{dep}"] > (df[f"features_bid-ask{dep}"].rolling(rol).agg("mean"))
        df[f"features_bid-ask{dep}"] = df[f"features_bid-ask{dep}"] > 0
    dep_cols = [c for c in df.columns if "ask" in c or "bid" in c and "feature" in c]
    for shift in range(1, 2):
        for c in dep_cols:
            df[c + f"_shift_{shift}"] = df[c].shift(shift)

    feats = [c for c in df.columns if "feature" in c]# + dep_shifts_cols
    
    for k in range(7):
        df[f"feature_dow_{k}"] = df.index % 7 == k
    
    df["feature_dow"] = df["feature_dow_0"] + df["feature_dow_2"] + df["feature_dow_5"]
    
    for f in feats:
        df[f] = df[f] > 0
#     print(len(feats))
#     evaluate(df, feats)
    
    return df, feats

def get_model(df, feats):
    df_for_train = df[df.isna().sum(axis = 1) == 0].reset_index(drop = True)
    model = Ridge(10)
    th = 500
    model.fit(df_for_train[feats], np.clip(df_for_train["target"], -th, th))
    return model

def logic():
#     data = get_btc_ohlcv()
#     c = data['close'].values
#     o = data['open'].values
#     pos = c[-2] - o[-2]
    
    df = get_data()
    df, feats = feature_engineering(df)
#     model = get_model(df, feats)
#     p = model.predict(df[feats].values[-1].reshape(1, -1))
    df["p"] = (df["features_bid-ask20_vs_roll14"] == True) * 1 + (df["feature_c-o_shift_1"] == True) +\
        (df["feature_c-o_eth_shift_1"] == False) / 3
    
    p = df["p"].values[-1]
    #p = np.random.randn()
    message = f"prediction rule : {p}"
    print(message)
    discord_Notify(message)
    
    return p

