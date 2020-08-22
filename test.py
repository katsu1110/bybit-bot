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

import argparse
from distutils.util import strtobool

config = get_config()
discord_url = config['discord_url']
apis = [
    config['api'],
    config['secret']
]
bybit = pybybit.API(*apis, testnet=config['testnet'])
discord_Notify(f"start!!! {datetime.datetime.now()}")

