from BybitAcct import BybitAcct
import json, time, math
import mplfinance as mpf
import pandas as pd
import datetime as dt
import pandas as pd
import matplotlib.animation as animation

def main():
    global client
    key, priv = loadConfig()
    client = BybitAcct(key, priv)
    fig = mpf.figure()
    ax = fig.add_subplot()
    return fig, ax, client

def animateFunc(ival):
    global timeP
    global client
    global ax
    data = getDict(client, timeP)
    ax.clear()
    mpf.plot(data,ax=ax, type='candle')

def getDict(client, timeP) -> pd.DataFrame:
    now: float = time.time()
    start: int = math.floor(now - (200 * int(timeP) * 60))
    data: dict = client.getPriceData(timeP, start)['result']
    ohlcDict: dict = {'Open': [], 'High': [], 'Low': [], 'Close': []}
    dates = []
    for val in data:
        ohlcDict['Open'].append(float(val['open']))
        ohlcDict['High'].append(float(val['high']))
        ohlcDict['Low'].append(float(val['low']))
        ohlcDict['Close'].append(float(val['close']))
        dates.append(dt.datetime.utcfromtimestamp(val['open_time']).strftime('%m-%d-%Y %H:%M:%S'))
    index = pd.DatetimeIndex(dates)
    df = pd.DataFrame.from_dict(ohlcDict)
    df.set_index(index, inplace=True)
    return df

def connect():
    key, priv = loadConfig()
    client = BybitAcct(key, priv)
    return client

def loadConfig():
    confFile = json.load(open('./config.json', 'r'))
    return confFile['key'], confFile['secret']

timeP=None
client=None
ax=None
def updateChart(q, x):
    global timeP
    global client
    global ax
    timeP = x
    fig, ax, client = main()
    ani = animation.FuncAnimation(fig, animateFunc, interval=200)
    mpf.show()
