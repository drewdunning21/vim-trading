import curses, math, time, json
from BybitAcct import BybitAcct
from multiprocessing import Process, Queue
from priceWindow import priceWindow
# from priceUpdate import getPrices
# from posUpdater import getPos
# from balUpdater import getBal
# from chart import updateChart

def main(scr):
    initColors()
    conf = loadConfig()
    client = connect(scr, conf)
    scr.nodelay(1)
    wins = getWins(scr)
    while 1:
        runUpdaters(wins)
        time.sleep(.01)

def runUpdaters(wins):
    for key, val in wins.items():
        wins[key].updateDisp()

''' INITIALIZE FUCTIONS '''

def getWins(scr):
    y, x = scr.getmaxyx()
    wins = {}
    wins['priceWin'] = priceWindow(scr, 3, 40, y//4, x//2-20)
    return wins

# connect to bybit
def connect(scr, conf):
    y, x = scr.getmaxyx()
    msg = 'Connecting...'
    scr.addstr(y // 2, x // 2 - len(msg)//2, msg)
    scr.refresh()
    key, priv = conf['key'], conf['secret']
    client = BybitAcct(key, priv)
    scr.clear()
    scr.refresh()
    return client

# initializes the color pairs
def initColors():
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.curs_set(False)

# loads the config data
def loadConfig() -> dict:
    return json.load(open('./config.json', 'r'))

def saveConfig(conf: dict):
    with open('config.json', 'w') as fp:
        json.dump(conf, fp)

if __name__ == '__main__':
    curses.wrapper(main)
