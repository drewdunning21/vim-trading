from BybitAcct import BybitAcct
import json

def getPos(q,x):
    key, priv = loadConfig()
    client = BybitAcct(key, priv)
    while 1:
        pos = client.getPositions('BTCUSD')
        q.put(pos)

def loadConfig():
    confFile = json.load(open('./config.json', 'r'))
    return confFile['key'], confFile['secret']
