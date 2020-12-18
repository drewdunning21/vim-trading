from BybitAcct import BybitAcct
import time
import json

def getBal(q,x):
    key, priv = loadConfig()
    client = BybitAcct(key, priv)
    while 1:
        pos = client.getBalance('BTC')
        q.put(pos)
        time.sleep(1)

def loadConfig():
    confFile = json.load(open('./config.json', 'r'))
    return confFile['key'], confFile['secret']
