from BybitAcct import BybitAcct
from pprint import pprint
import curses
import json

def main(scr):
    key, priv = loadConfig()
    # key, priv = loadConfig()
    client = BybitAcct(key, priv)
    client.chaseBuy('BTCUSD', 4000)

    print(scr.getmaxyx())
    curses.curs_set(0)
    col = 0
    menuItems = ['Buy', 'Sell']
    quit()
    while 1:
        key = scr.getch()
        if key == ord('e') and col != 0:
            # up
            col -= 1
            vMenu(scr, col, menuItems)
        elif key == ord('n') and col != len(menuItems) - 1:
            # down
            col += 1
            vMenu(scr, col, menuItems)

def vMenu(scr, col, menuItems):
    scr.clear()
    h, w = scr.getmaxyx()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    for i, val in enumerate(menuItems):
        x = w//2 - len(val)//2
        y = h//2 - len(menuItems) + i
        if col == i:
            scr.attron(curses.color_pair(1))
            scr.addstr(y,x,val)
            scr.attroff(curses.color_pair(1))
        else:
            scr.addstr(y,x,val)
    scr.refresh()

def hMenu(scr, row, menuItems):
    scr.clear()
    h, w = scr.getmaxyx()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    for i, val in enumerate(menuItems):
        x = w//2 - len(val)//2
        y = h//2 - len(menuItems) + i
        if row == i:
            scr.attron(curses.color_pair(1))
            scr.addstr(y,x,val)
            scr.attroff(curses.color_pair(1))
        else:
            scr.addstr(y,x,val)
    scr.refresh()

def loadConfig():
    confFile = json.load(open('./config.json', 'r'))
    return confFile['key'], confFile['secret']




curses.wrapper(main)
