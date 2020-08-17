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
    
    ## bct ohlc
    df["feature_c-o"] = (df["close"] - df["open"])
    df["feature_h-c"] = (df["high"] - df["close"])
    df["feature_l-c"] = (df["low"] - df["close"])
    df["feature_h-o"] = (df["high"] - df["open"])
    df["feature_l-o"] = (df["low"] - df["open"])
    df["feature_h-l"] = (df["high"] - df["low"])

    feats = ["feature_c-o", "feature_h-c", "feature_l-c", "feature_h-o", "feature_l-o", "feature_h-l"]
    for shift in range(1, 4):
        for f in feats:
            df[f + f"_shift_{shift}"] = df[f].shift(shift)
    feats = [c for c in df.columns if "feature" in c]
    for f in feats:
        for rol in [7, 14, 28, 60, 120]:
            df[f"{f}_vs_roll{rol}"] = df[f] > (df[f].rolling(rol).agg("mean"))
    for diff in range(1, 4):
        for f in feats:
            df[f + f"_diff_{diff}"] = df[f].diff(diff)
            
            
    ## eth ohlc
    df["feature_c-o_eth"] = (df["close_eth"] - df["open_eth"])
    df["feature_h-c_eth"] = (df["high_eth"] - df["close_eth"])
    df["feature_l-c_eth"] = (df["low_eth"] - df["close_eth"])
    df["feature_h-o_eth"] = (df["high_eth"] - df["open_eth"])
    df["feature_l-o_eth"] = (df["low_eth"] - df["open_eth"])
    df["feature_h-l_eth"] = (df["high_eth"] - df["low_eth"])

    feats = ["feature_c-o_eth", "feature_h-c_eth", "feature_l-c_eth", "feature_h-o_eth", "feature_l-o_eth", "feature_h-l_eth"]
    for shift in range(1, 4):
        for f in feats:
            df[f + f"_shift_{shift}"] = df[f].shift(shift)
    for f in feats:
        for rol in [7, 14, 28, 60, 120]:
            df[f"{f}_vs_roll{rol}"] = df[f] > (df[f].rolling(rol).agg("mean"))
            df[f"{f}_roll{rol}"] = df[f].rolling(rol).agg("mean") > 0
    for diff in range(1, 4):
        for f in feats:
            df[f + f"_diff_{diff}"] = df[f].diff(diff)
            
            
    ## depth
    for dep in [5, 10, 20, 30, 50, 90]:
        df[f"features_bid-ask{dep}"] = df[f"bids{dep}"] - df[f"asks{dep}"]
        for rol in [7, 14, 28, 60, 120]:
            df[f"features_bid-ask{dep}_vs_roll{rol}"] = df[f"features_bid-ask{dep}"] - df[f"features_bid-ask{dep}"].rolling(rol).agg("mean")
    dep_cols = [c for c in df.columns if (("ask" in c) or ("bid" in c)) and "feature" in c]
    for shift in range(1, 4):
        for c in dep_cols:
            df[c + f"_shift_{shift}"] = df[c].shift(shift)
    for diff in range(1, 4):
        for f in dep_cols:
            df[f + f"_diff_{diff}"] = df[f].diff(diff)
            
    
    ## dow
    df["weekday"] = df["time"].apply(lambda x : x.weekday())
    for k in range(7):
        df[f"feature_dow_{k}"] = df["weekday"] == k
    
    df["feature_dow"] = df["feature_dow_0"] + df["feature_dow_2"]# + df["feature_dow_4"] + df["feature_dow_5"]
    
    ## others
    feats = ["volume", "trades_eth", "volume_eth", "vwap_eth"]
    feats = ["features_" + f for f in feats]
    for f in feats:
        df[f] = df["_".join(f.split("_")[1:])]
    for shift in range(1, 4):
        for f in feats:
            df[f + f"_shift_{shift}"] = df[f].shift(shift)
    for f in feats:
        for rol in [7, 14, 28, 60, 120]:
            df[f"{f}_vs_roll{rol}"] = df[f] > (df[f].rolling(rol).agg("mean"))
            df[f"{f}_roll{rol}"] = df[f].rolling(rol).agg("mean") > 0
    for diff in range(1, 4):
        for f in feats:
            df[f + f"_diff_{diff}"] = df[f].diff(diff)
    
    
    feats = [c for c in df.columns if "feature" in c]# + dep_shifts_cols
    for f in feats:
        df[f] = df[f] > 0
        
    df["feature_rule1"] = (df["features_bid-ask20_vs_roll14"] == True) * 1 + (df["feature_c-o_shift_1"] == True) * 1 +\
        (df["feature_c-o_eth_shift_1"] == False) * 1
    df["feature_rule1"] = df["feature_rule1"] / 3
    
    df["feature_rule2"] = (df["features_bid-ask20_vs_roll14"] == True) * 1 + (df["feature_c-o_shift_1"] == True) * 1 +\
    (df["feature_c-o_eth_shift_1"] == False) * 1 + (df["feature_l-o_shift_1_diff_1"] == True) * 1 +\
    (df["features_bid-ask90_vs_roll60"] == True) * 1
    df["feature_rule2"] = df["feature_rule2"] / 5
    
    df["feature_rule3"] = (df["features_bid-ask20_vs_roll14"] == True) * 1 + (df["feature_c-o_shift_1"] == True) * 1 +\
    (df["feature_c-o_eth_shift_1"] == False) * 1 + (df["feature_l-o_shift_1_diff_1"] == True) * 1 +\
    (df["features_bid-ask20_vs_roll60"] == True) * 1 + (df["features_bid-ask20_vs_roll60"] == True) * 1 +\
    (df["feature_dow"] == False) * 1
    df["feature_rule3"] = df["feature_rule3"] / 7
    
    df["feature_rule4"] = (df["features_bid-ask20_vs_roll14"] == True) * 1 + (df["feature_c-o_shift_1"] == True) * 1 +\
    (df["feature_c-o_eth_shift_1"] == False) * 1 + (df["feature_l-o_shift_1_diff_1"] == True) * 1 +\
    (df["features_bid-ask20_vs_roll60"] == True) * 1 + (df["features_bid-ask20_vs_roll60"] == True) * 1 +\
    (df["features_volume_vs_roll120"] == True) * 1    
    df["feature_rule4"] = df["feature_rule4"] / 7
    
    return df, feats

def get_model(df, feats):
    df_for_train = df[df.isna().sum(axis = 1) == 0].reset_index(drop = True)
    model = Ridge(10)
    th = 500
    model.fit(df_for_train[feats], np.clip(df_for_train["target"], -th, th))
    return model


def logic():
    df = get_data()
    df, feats = feature_engineering(df)
    p = pred_logic(df, feats)
    return p
    

def pred_logic(df, feats, send = True):
    df["p1"] = (df["features_bid-ask20_vs_roll14"] == True) * 1
    df["p2"] = (df["feature_c-o_shift_1"] == True) * 1
    df["p3"] = (df["feature_c-o_eth_shift_1"] == False) * 1
    df["p4"] = (df["feature_l-o_shift_1_diff_1"] == True) * 1
    df["p5"] = (df["features_bid-ask90_vs_roll60"] == True) * 1
    
    df["p"]  = (df["p1"] + df["p2"] + df["p3"] + df["p4"] + df["p5"]) / 5
    
    p = df["p"].values[-1]
    p1 = df["p1"].values[-1]
    p2 = df["p2"].values[-1]
    p3 = df["p3"].values[-1]
    p4 = df["p4"].values[-1]
    p5 = df["p5"].values[-1]
    #p = np.random.randn()
    if send:
        message = f"prediction rule : {p}, rule1 : {p1}, rule2 : {p2}, rule3 : {p3}, rule4 : {p4}, rule5 : {p5}"
        print(message)
        discord_Notify(message)
#     aaaaaaaaaaaaaaa
    p = p > 0.5
    return p


def test_logic():
    df = get_data()
    df, feats = feature_engineering(df)

    t = "2020-01-01"
    k_start = np.where(df["time"] == datetime.datetime.strptime(t, '%Y-%m-%d'))[0][0]

    r = 0
    rs = []
    long_count = 0
    long_win = 0
    short_count = 0
    short_win = 0
    for k in range(k_start, len(df) - 1):
        pred = pred_logic(df.iloc[:k], feats, send = False)
        co = (df.iloc[k]["close"] - df.iloc[k]["open"])
        if pred > 0:
            r += co
            long_count += 1
            if co > 0:
                long_win += 1
        else:
            r -= co
            short_count += 1
            if co < 0:
                short_win += 1
        print(df.iloc[k]["time"], r)
    print(f"r sum : {r}, r mean : {r/(len(df) - k_start)}")
    print(f"long  win : {long_win}/{long_count}  = {long_win/long_count}")
    print(f"short win : {short_win}/{short_count}  = {short_win/short_count}")
    # import matplotlib.pyplot as plt
    # plt.plot(rs)
    # plt.show()
    
if __name__ == "__main__":
    test_logic()