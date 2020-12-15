from BybitAcct import BybitAcct
import curses
import json
import pprint
import time
import math

def displayChart(scr, client: BybitAcct, period: str):
    y, x = scr.getmaxyx()
    scr.clear()
    scr.addstr(y//2, x//2, 'Loading...')
    scr.refresh()
    now: float = time.time()
    start: int = math.floor(now - (now % 3600)) - (200 * 3600)
    data: dict = client.getPriceData(period, start)
    scr.clear()
    scr.attron(curses.color_pair(3))
    scr.addstr(y//2, x//2, ' ')
    scr.attroff(curses.color_pair(3))
    scr.refresh()
    key: int = -1
    while key != ord('t'):
        key = scr.getch()


def connect():
    key, priv = loadConfig()
    client = BybitAcct(key, priv)
    return client

def loadConfig():
    confFile = json.load(open('./config.json', 'r'))
    return confFile['key'], confFile['secret']
