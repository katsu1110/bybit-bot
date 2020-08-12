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

    df["feature_c-o"] = (df["close"] - df["open"]) > 0
    df["feature_h-c"] = (df["high"] - df["close"]) > 0
    df["feature_l-c"] = (df["low"] - df["close"]) > 0
    df["feature_h-o"] = (df["high"] - df["open"]) > 0
    df["feature_l-o"] = (df["low"] - df["open"]) > 0
    df["feature_h-l"] = (df["high"] - df["low"]) > 0

    feats = ["feature_c-o", "feature_h-c", "feature_l-c", "feature_h-o", "feature_l-o", "feature_h-l"]
    for shift in range(1, 3):
        for f in feats:
            df[f + f"_shift_{shift}"] = df[f].shift(shift)

    for dep in [20, 30, 50, 90]:
        df[f"features_bid-ask{dep}"] = df[f"bids{dep}"] - df[f"asks{dep}"]
        for rol in [7, 14]:
            df[f"features_bid-ask{dep}_vs_roll{rol}"] = df[f"features_bid-ask{dep}"] > (df[f"features_bid-ask{dep}"].rolling(rol).agg("mean"))
        df[f"features_bid-ask{dep}"] = df[f"features_bid-ask{dep}"] > 0
    dep_cols = [c for c in df.columns if "ask" in c or "bid" in c and "feature" in c]
    # for shift in range(1, 2):
    #     for c in dep_cols:
    #         df[c + f"_shift_{shift}"] = df[c].shift(shift)

    feats = [c for c in df.columns if "feature" in c]# + dep_shifts_cols
#     print(len(feats))
#     evaluate(df, feats)
    
    return df, feats

def get_model(df, feats):
    df_for_train = df[df.isna().sum(axis = 1) == 0].reset_index(drop = True)
    model = Ridge(0.1)
    model.fit(df_for_train[feats], df_for_train["target"])
    return model


def logic():
#     data = get_btc_ohlcv()
#     c = data['close'].values
#     o = data['open'].values
#     pos = c[-2] - o[-2]
    
    df = get_data()
    df, feats = feature_engineering(df)
    model = get_model(df, feats)
    p = model.predict(df[feats].values[-1].reshape(1, -1))
    
    p = np.random.randn()
    message = f"prediction : {p}"
    print(message)
    discord_Notify(message)
    
    return p

