import curses, math, time, json
from BybitAcct import BybitAcct
from windows.priceWindow import priceWindow
from windows.posWindow import posWindow
from windows.balWindow import balWindow
from windows.menuWindow import menuWindow
from typing import Any

def main(scr: Any) -> None:
    initColors()
    conf: dict  = loadConfig()
    client: BybitAcct = connect(scr, conf)
    scr.nodelay(1)
    wins: dict = getWins(scr)
    y, x = scr.getmaxyx()
    menu: menuWindow = menuWindow(scr, 3, x, y//2-1, 0, ['Buy', 'Sell'], 1)
    while 1:
        key = scr.getch()
        runUpdaters(wins)
        # left
        if key == ord('m'):
            menu.makeMenu(menu.getSel() - 1)
        # right
        if key == ord('i'):
            menu.makeMenu(menu.getSel() + 1)
        time.sleep(.01)

def runUpdaters(wins: dict) -> None:
    for val in wins.values():
        val.updateDisp()

''' INITIALIZE FUCTIONS '''

def getWins(scr: Any) -> dict:
    x: int = 0
    y: int = 0
    y, x = scr.getmaxyx()
    wins: dict = {}
    wins['priceWin'] = priceWindow(scr, 3, 40, y//4, x//2-20)
    wins['posWin'] = posWindow(scr, 4, 80, y - (y//4), x//2-40)
    wins['balWin'] = balWindow(scr, 3, 30, 1, x - x//4, wins['priceWin'])
    return wins

# connect to bybit
def connect(scr: Any, conf: dict) -> BybitAcct:
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
def initColors() -> None:
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.curs_set(False)

# loads the config data
def loadConfig() -> dict:
    return json.load(open('./config.json', 'r'))

def saveConfig(conf: dict) -> None:
    with open('config.json', 'w') as fp:
        json.dump(conf, fp)

if __name__ == '__main__':
    curses.wrapper(main)
