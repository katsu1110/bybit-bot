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
    df["ho"] = (df["high"] - df["open"]).shift(-1)
    df["ol"] = (df["open"] - df["low"]).shift(-1)
    
    ## bct ohlc
    df["feature_c-o"] = (df["close"] - df["open"])
    df["feature_h-c"] = (df["high"] - df["close"])
    df["feature_l-c"] = (df["low"] - df["close"])
    df["feature_h-o"] = (df["high"] - df["open"])
    df["feature_l-o"] = (df["low"] - df["open"])
    df["feature_h-l"] = (df["high"] - df["low"])
    df["feature_h-o-c-l"] = (df["high"] - df["open"]) - (df["close"] - df["low"])
    df["feature_h-c-o-l"] = (df["high"] - df["close"]) - (df["open"] - df["low"])
    df["feature_hige_comp"] = df["feature_h-o-c-l"]
    df.loc[df["feature_c-o"] > 0, "feature_hige_comp"] = df["feature_h-c-o-l"]
    

    feats = ["feature_c-o", "feature_h-c", "feature_l-c", "feature_h-o",
             "feature_l-o", "feature_h-l", "feature_h-o-c-l", "feature_h-c-o-l", "feature_hige_comp"]
    for shift in range(1, 4):
        for f in feats:
            df[f + f"_shift_{shift}"] = df[f].shift(shift)
    feats = [c for c in df.columns if "feature" in c]
    for f in feats:
        for rol in [7, 14, 28, 60, 120]:
            df[f"{f}_vs_roll{rol}"] = df[f] > (df[f].rolling(rol).agg("mean"))
    for f in feats:
        for rol1 in [7, 14, 28, 60, 120]:
            for rol2 in [7, 14, 28, 60, 120]:
                df[f"{f}_roll{rol1}_vs_roll{rol2}"] = (df[f].rolling(rol1).agg("mean")) > (df[f].rolling(rol2).agg("mean"))
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
    df["feature_h-o-c-l_eth"] = (df["high_eth"] - df["open_eth"]) - (df["close_eth"] - df["low_eth"])
    df["feature_h-c-o-l_eth"] = (df["high_eth"] - df["close_eth"]) - (df["open_eth"] - df["low_eth"])
    df["feature_hige_comp_eth"] = df["feature_h-o-c-l_eth"]
    df.loc[df["feature_c-o_eth"] > 0, "feature_hige_comp_eth"] = df["feature_h-c-o-l_eth"]

    
    feats = ["feature_c-o_eth", "feature_h-c_eth", "feature_l-c_eth",
             "feature_h-o_eth", "feature_l-o_eth", "feature_h-l_eth",
            "feature_h-o-c-l_eth", "feature_h-c-o-l_eth", "feature_hige_comp_eth"]
    for shift in range(1, 4):
        for f in feats:
            df[f + f"_shift_{shift}"] = df[f].shift(shift)
    for f in feats:
        for rol in [7, 14, 28, 60, 120]:
            df[f"{f}_vs_roll{rol}"] = df[f] > (df[f].rolling(rol).agg("mean"))
            df[f"{f}_roll{rol}"] = df[f].rolling(rol).agg("mean") > 0
    for f in feats:
        for rol1 in [7, 14, 28, 60, 120]:
            for rol2 in [7, 14, 28, 60, 120]:
                df[f"{f}_roll{rol1}_vs_roll{rol2}"] = (df[f].rolling(rol1).agg("mean")) > (df[f].rolling(rol2).agg("mean"))
    for diff in range(1, 4):
        for f in feats:
            df[f + f"_diff_{diff}"] = df[f].diff(diff)
            
            
    ## depth
    deps = [5, 10, 20, 30, 50, 90]
    for dep in deps:
        df[f"features_bid-ask{dep}"] = df[f"bids{dep}"] - df[f"asks{dep}"]
        for rol in [7, 14, 28, 60, 120]:
            df[f"features_bid-ask{dep}_vs_roll{rol}"] = df[f"features_bid-ask{dep}"] - df[f"features_bid-ask{dep}"].rolling(rol).agg("mean")
            
            
    for dep in deps:
        for dep2 in deps:
            if dep == dep2:
                continue
            df[f"features_bid-ask{dep}-{dep2}"] = df[f"bids{dep}"] - df[f"asks{dep2}"]
            for rol in [7, 14, 28, 60, 120]:
                df[f"features_bid-ask{dep}-{dep2}_vs_roll{rol}"] = df[f"features_bid-ask{dep}-{dep2}"] - df[f"features_bid-ask{dep}-{dep2}"].rolling(rol).agg("mean")
    
    for dep in deps:
        for rol1 in [7, 14, 28, 60, 120]:
            for rol2 in [7, 14, 28, 60, 120]:
                df[f"features_bid-ask{dep}_roll{rol1}_vs_roll{rol2}"] = df[f"features_bid-ask{dep}"].rolling(rol1).agg("mean") - df[f"features_bid-ask{dep}"].rolling(rol2).agg("mean")
    
    for k in range(len(deps) - 1):
        df[f"features_bid_{deps[k+1]}-{deps[k]}"] = df[f"bids{deps[k+1]}"] - df[f"bids{deps[k]}"]
        df[f"features_ask_{deps[k+1]}-{deps[k]}"] = df[f"asks{deps[k+1]}"] - df[f"asks{deps[k]}"]
        
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
    (df["feature_h-c-o-l_eth_roll28_vs_roll60"] == True) * 1
    df["feature_rule3"] = df["feature_rule3"] / 7
    
    df["feature_rule4"] = (df["feature_l-c_vs_roll7"] == True) * 1 +\
    (df["features_bid-ask5_diff_1"] == True) * 1 +\
    (df["features_bid-ask20_roll14_vs_roll28"] == True) * 1 +\
    (df["feature_c-o_vs_roll14"] == False) * 1 +\
    (df["feature_c-o"] == False) * 1 +\
    (df["feature_dow"] == False) * 1
    df["feature_rule4"] = df["feature_rule4"] / 6
    
    df["feature_rule5"] = (df["feature_rule4"] + df["feature_rule2"])/2
    
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
    p = df["feature_rule5"].values[-1]
    #p = np.random.randn()
    if send:
        message = f"prediction : {p}"
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
    max_down = 0
    for k in range(k_start, len(df) - 1):
        pred = pred_logic(df.iloc[:k], feats, send = False)
        co = (df.iloc[k]["close"] - df.iloc[k]["open"])
        if pred > 0:
            r += co
            long_count += 1
            max_down = -min([-max_down, co])
            if co > 0:
                long_win += 1
        else:
            r -= co
            short_count += 1
            max_down = max([max_down, co])
            if co < 0:
                short_win += 1
        print(df.iloc[k]["time"], r)
    print(f"r sum : {r}, r mean : {r/(len(df) - k_start)}")
    print(f"long  win : {long_win}/{long_count}  = {long_win/long_count}")
    print(f"short win : {short_win}/{short_count}  = {short_win/short_count}")
    print(f"max down : {max_down}")
    # import matplotlib.pyplot as plt
    # plt.plot(rs)
    # plt.show()
    
if __name__ == "__main__":
    test_logic()
