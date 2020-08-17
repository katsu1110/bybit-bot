import time
import datetime
import requests
from config import get_config

def discord_Notify(message, fileName=None):
    
    
    config = get_config()
    url = config['discord_url']
    
    payload = {"content": " " + message + " "}
    if fileName == None:
        try:
            requests.post(url, data=payload)
        except:
            pass
    else:
        try:
            files = {"imageFile": open(fileName, "rb")}
            requests.post(url, data=payload, files=files)
        except:
            pass
    
    slack_send(message)
    slack_send(config["slack_daily_message"])

def slack_send(message):
    config = get_config()
    param = {
            'token': config["slack_token"],
            'channel': config["slack_channel"],
            'text': message,
            "user_name" : "bot"
        }
    requests.post("https://slack.com/api/chat.postMessage", data=param)
