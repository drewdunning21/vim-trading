from BybitAcct import BybitAcct
import json
import curses

def getPrices(q,x):
    key, priv = loadConfig()
    client = BybitAcct(key, priv)
    while 1:
        spread = client.getSpread('BTCUSD')
        q.put((spread['bid']['price'],spread['ask']['price']))

def loadConfig():
    confFile = json.load(open('./config.json', 'r'))
    return confFile['key'], confFile['secret']

