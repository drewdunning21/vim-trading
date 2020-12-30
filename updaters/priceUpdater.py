from BybitAcct import BybitAcct
import json
import time

def getPrices(q,x):
    key, priv = loadConfig()
    client = BybitAcct(key, priv)
    count = 0
    while 1:
        count += 1
        spread = client.getSpread('BTCUSD')
        q.put((spread['bid']['price'],spread['ask']['price']))
        time.sleep(1)

def loadConfig():
    confFile = json.load(open('./config.json', 'r'))
    return confFile['key'], confFile['secret']
