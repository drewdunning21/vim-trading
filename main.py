from BybitAcct import BybitAcct
import time
from pprint import pprint
import curses
import json
import logging as log
import curses.textpad as textpad
from subprocess import Popen, PIPE
from multiprocessing import Process, Queue
from priceUpdate import getPrices

def main(scr):
    key, priv = loadConfig()
    setupLogger()
    client = BybitAcct(key, priv)
    curses.curs_set(0)
    col = 0
    menuItems = ['Buy', 'Sell']
    log.info('other here')
    hMenu(scr, col, menuItems)
    p, q = startUpdater(scr)
    scr.nodelay(1)
    while 1:
        updatePriceDisp(scr, q)
        key = scr.getch()
        if key == ord('m') and col != 0:
            # left
            col -= 1
            hMenu(scr, col, menuItems)
        elif key == ord('i') and col != len(menuItems) - 1:
            # right
            col += 1
            hMenu(scr, col, menuItems)
        elif key == 10:
            scr.clear()
            orderPage(scr, col, client, col, q)
            hMenu(scr, col, menuItems)

def orderPage(scr, order, client, side, q):
    updatePriceDisp(scr, q)
    menuItems = ['Market', 'Limit', 'Chase']
    col = 1
    hMenu(scr, col, menuItems)
    side = 'Buy' if side == 0 else 'Sell'
    while 1:
        updatePriceDisp(scr, q)
        key = scr.getch()
        if key == ord('m') and col != 0:
            # left
            col -= 1
            hMenu(scr, col, menuItems)
        elif key == ord('i') and col != len(menuItems) - 1:
            # right
            col += 1
            hMenu(scr, col, menuItems)
        elif key == 10:
            scr.clear()
            if col == 0:
                marketOrder(scr, client, side, q)
            elif col == 1:
                limitOrder(scr, client, side, q)
            else:
                chaseOrder(scr, client, side, q)
            return

def marketOrder(scr, client, side, q):
    updatePriceDisp(scr, q)
    amnt = getAmnt(scr, q)
    client.marketOrder('BTCUSD', amnt, side)

def limitOrder(scr, client, side, q):
    amnt = getAmnt(scr, q)
    price = getPrice(scr, client, side)
    client.limitOrder('BTCUSD', amnt, price, side)

def chaseOrder(scr, client, side, q):
    client.chaseBuy()

def startUpdater(scr):
    q = Queue()
    p = Process(target=getPrices, args=(q, 1))
    p.start()
    return p, q

def getPrice(scr, client, side):
    # change alot
    scr.clear()
    scr.refresh()
    scr.nodelay(True)
    while 1:
        key = scr.getch()
        if key == -1: continue
    return 0

def updatePriceDisp(scr, q):
    start = time.time()
    printt('starting update')
    printt(start)
    try:
        bid, ask = q.get(False)
    except Exception as e:
        printt(e)
        return
    printt('got prices. fixing now')
    printt(time.time() - start)
    bid, ask = fixPrice(bid), fixPrice(ask)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    y, x = scr.getmaxyx()
    # displays the bid
    scr.attron(curses.color_pair(2))
    scr.addstr(y // 4, x // 2 - 5 - len(bid), bid)
    scr.attroff(curses.color_pair(2))
    # displays the ask
    scr.attron(curses.color_pair(1))
    scr.addstr(y // 4, x // 2 + 5, ask)
    scr.attroff(curses.color_pair(1))
    scr.refresh()
    printt('done')
    printt(time.time() - start)
    printt('\n')

def fixPrice(price):
    return price + '.00' if price[-2] != '.' else price + '0'

def getAmnt(scr, q):
    scr.clear()
    y, x = scr.getmaxyx()
    msg = 'Enter size ($)'
    scr.addstr(y//2 - 3,x//2 - (len(msg)//2),msg)
    box = curses.newwin(3, 50, y // 2 - 2, x // 2 - 25)
    box.border()
    scr.refresh()
    box.refresh()
    amnt = ''
    spot = x // 2 - 22
    scr.addstr(y // 2 - 1, spot - 1, '$')
    updatePriceDisp(scr, q)
    while 1:
        key = scr.getkey()
        updatePriceDisp(scr, q)
        if '\n' in key:
            return float(amnt)
        elif key == '' and len(amnt) != 0:
            amnt = amnt[:-1]
            # scr.delch(y // 2 - 1, spot - 2)
            scr.addstr(y // 2 - 1, spot - 2, ' ')
            rewriteNum(scr, amnt, x, y)
            spot -= 1
            if len(amnt) % 3 == 0:
                scr.addstr(y // 2 - 1, spot - 2, ' ')
                spot -= 1
        elif key.isnumeric() or key == '.':
            amnt += key
            rewriteNum(scr, amnt, x, y)
            if (len(amnt) - 1) % 3 == 0: spot += 1
            spot += 1

def rewriteNum(scr, amnt, x, y):
    spot = x // 2 - 22
    copy = amnt * 1
    commas = 0
    for val in copy:
        scr.addstr(y // 2 - 1, spot, val)
        spot += 1
        amnt = amnt[1:]
        if len(amnt) % 3 == 0 and len(amnt) != 0:
            commas += 1
            scr.addstr(y // 2 - 1, spot, ',')
            spot += 1
    return commas

def vMenu(scr, row, menuItems):
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

def hMenu(scr, col, menuItems):
    if len(menuItems) % 2 != 0: oddMenu(scr, col, menuItems)
    else: evenMenu(scr, col, menuItems)

def evenMenu(scr, col, menuItems):
    # scr.clear()
    h, w = scr.getmaxyx()
    y = h//2
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    x = w//2 - (10 * (len(menuItems)//2))
    for i, val in enumerate(menuItems):
        x += len(val) // 2 + 1
        if col == i:
            scr.attron(curses.color_pair(1))
            scr.addstr(y,x,val)
            scr.attroff(curses.color_pair(1))
        else:
            scr.addstr(y,x,val)
        x += 10
    scr.refresh()

def oddMenu(scr, col, menuItems):
    # scr.clear()
    h, w = scr.getmaxyx()
    y = h//2
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    for i, val in enumerate(menuItems):
        x = w//2 - (10 * ((len(menuItems)//2) - i)) - (len(val)//2)
        if col == i:
            scr.attron(curses.color_pair(1))
            scr.addstr(y,x,val)
            scr.attroff(curses.color_pair(1))
        else:
            scr.addstr(y,x,val)
    scr.refresh()

def loadConfig():
    confFile = json.load(open('./config.json', 'r'))
    return confFile['key'], confFile['secret']

def setupLogger():
    log.basicConfig(filename='log.log',  level=log.DEBUG)

def printt(txt):
    file = open('text.txt', 'a')
    file.write(str(txt) + '\n')
    file.close()

if __name__ == '__main__':
    curses.wrapper(main)
