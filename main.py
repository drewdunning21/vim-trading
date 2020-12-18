from BybitAcct import BybitAcct
import curses
import json
from multiprocessing import Process, Queue
from priceUpdate import getPrices
from posUpdater import getPos
from balUpdater import getBal
import math
import time

def main(scr):
    client = connect(scr)
    initColors()
    procs, qs = startUpdaters()
    scr.nodelay(1)
    col = 0
    menuItems = ['Buy', 'Sell']
    hMenu(scr, col, menuItems)
    btc = True
    while 1:
        runUpdaters(scr, qs, btc)
        key = scr.getch()
        if key == ord('m') and col != 0:
            # left
            col -= 1
        elif key == ord('i') and col != len(menuItems) - 1:
            # right
            col += 1
        elif key == 10 or key == ord('t'):
            scr.clear()
            orderPage(scr, col, client, col, qs, btc)
        elif key == ord('d'):
            btc = not btc
        hMenu(scr, col, menuItems)
        time.sleep(.01)

def startUpdaters():
    uP, uQ = startPriceUpdater()
    pP, pQ = startPosUpdater()
    bP, bQ = startBalUpdater()
    return [uP, pP, bP], [uQ, pQ, bQ]

def connect(scr):
    curses.curs_set(0)
    y, x = scr.getmaxyx()
    msg = 'Connecting...'
    scr.addstr(y // 2, x // 2 - len(msg)//2, msg)
    scr.refresh()
    key, priv = loadConfig()
    client = BybitAcct(key, priv)
    scr.clear()
    return client

def orderPage(scr, order, client, side, qs, btc):
    runUpdaters(scr, qs, btc)
    menuItems = ['Market', 'Limit', 'Chase']
    col = 1
    side = 'Buy' if side == 0 else 'Sell'
    while 1:
        hMenu(scr, col, menuItems)
        runUpdaters(scr, qs, btc)
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
            if col == 0:    order = marketOrder(scr, client, side, qs, btc)
            elif col == 1:  order = limitOrder(scr, client, side, qs, btc)
            else:           order = chaseOrder(scr, client, side, qs, btc)
            if order:
                scr.clear()
                return
        elif key == ord('s'):
            scr.clear()
            return
        time.sleep(.01)

def marketOrder(scr, client, side, qs, btc):
    runUpdaters(scr, qs, btc)
    amnt = getAmnt('Enter size ($)', scr, qs, btc)
    amnt = int(str(amnt).split('.')[0])
    if amnt == -1: return False
    client.marketOrder('BTCUSD', amnt, side)
    return True

def limitOrder(scr, client, side, qs, btc):
    amnt = getAmnt('Enter size ($)', scr, qs, btc)
    amnt = int(str(amnt).split('.')[0])
    if amnt == -1: return False
    price = getAmnt('Enter price ($)', scr, qs, btc)
    if price == -1: return False
    client.limitOrder('BTCUSD', amnt, price, side)
    return True

def chaseOrder(scr, client, side, qs, btc):
    amnt = getAmnt('Enter size ($)', scr, qs, btc)
    amnt = int(str(amnt).split('.')[0])
    if amnt == -1: return False
    if side == 'Buy':   chaseBuy(client, 'BTCUSD', amnt, qs, scr, btc)
    else:               chaseSell(client, 'BTCUSD', amnt, qs, scr, btc)
    return True

def chaseBuy(client: BybitAcct, symbol: str, amnt: int, qs, scr, btc, maxPrice=100000000):
    spread = client.getSpread(symbol)
    # make the initial order
    bid = float(spread['bid']['price'])
    orderId = client.limitOrder(symbol, amnt, bid, 'Buy')
    y, x = scr.getmaxyx()
    orderStatusPage(scr, '-', '-')
    status = ''
    if not orderId:
        return
    while status != 'Filled':
        runUpdaters(scr, qs, btc)
        spread = client.getSpread(symbol)
        newBid = float(spread['bid']['price'])
        # check if price greater than max price
        if newBid > maxPrice:
            return 0
        # if not, check if the cur bid is greater than cur order bid
        if newBid != bid:
            # if so, adjust cur order bid
            orderId = client.replaceOrder(orderId, symbol, str(newBid), str(amnt))
            bid = newBid
        orderStatus = client.getStatus(symbol, orderId)
        status = orderStatus['order_status']
        orderStatusPage(scr, orderStatus['cum_exec_qty'], orderStatus['qty'])
    return orderId

def chaseSell(client: BybitAcct, symbol: str, amnt: int, qs, scr, btc, minPrice=0):
    spread = client.getSpread(symbol)
    # make the initial order
    ask = float(spread['ask']['price'])
    orderId = client.limitOrder(symbol, amnt, ask, 'Sell')
    y, x = scr.getmaxyx()
    orderStatusPage(scr, '-', '-')
    status = ''
    if not orderId:
        return
    while status != 'Filled':
        runUpdaters(scr, qs, btc)
        spread = client.getSpread(symbol)
        newAsk = float(spread['ask']['price'])
        # check if price greater than max price
        if newAsk < minPrice:
            return 0
        # if not, check if the cur bid is greater than cur order bid
        if newAsk != ask:
            # if so, adjust cur order bid
            orderId = client.replaceOrder(orderId, symbol, str(newAsk), str(amnt))
            ask = newAsk
        orderStatus = client.getStatus(symbol, orderId)
        status = orderStatus['order_status']
        orderStatusPage(scr, orderStatus['cum_exec_qty'], orderStatus['qty'])
    return orderId

def orderStatusPage(scr, filled, total):
    y, x = scr.getmaxyx()
    msg = 'Filled Quantity: ' + str(filled) + ' / ' + str(total)
    scr.addstr(y//2 - 3, x // 2 - len(msg)//2, msg)
    if filled == '-': return
    perc: float = float(filled) / float(total)
    scr.attron(curses.color_pair(3))
    for i in range(math.floor(perc * 50)-1):
        scr.addstr(y//2-1, x//2-23 + i, ' ')
    scr.attroff(curses.color_pair(3))
    scr.refresh()

def makeBox(scr, h: int, w: int, y, x):
    box = curses.newwin(h, w, y, x)
    box.border()
    scr.refresh()
    box.refresh()
    return box

def startPriceUpdater():
    q = Queue()
    p = Process(target=getPrices, args=(q, 1))
    p.start()
    return p, q

def startPosUpdater():
    q = Queue()
    p = Process(target=getPos, args=(q, 1))
    p.start()
    return p, q

def startBalUpdater():
    q = Queue()
    p = Process(target=getBal, args=(q, 1))
    p.start()
    return p, q

def runUpdaters(scr, qs, btc):
    updatePriceDisp(scr, qs[0])
    updatePosDisp(scr, qs[1])
    updateBalDisp(scr, qs[2], btc)

prevBid = '00'
prevAsk = '00'
def updatePriceDisp(scr, q):
    global prevBid, prevAsk
    bid, ask = prevBid, prevAsk
    while not q.empty():
        bid, ask = q.get(False)
        prevBid, prevAsk = bid, ask
    bid, ask = fixPrice(bid), fixPrice(ask)
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

def updatePosDisp(scr, q):
    pos = None
    while not q.empty():
        pos = q.get(False)
    if pos is None: return
    y, x = scr.getmaxyx()
    startY, startX = math.floor(y * .7), x//2 - 40,
    # startY, startX = math.floor(y * .7), math.floor(x * .01)
    scr.attron(curses.color_pair(3))
    scr.addstr(startY, startX, 'Positions')
    scr.attroff(curses.color_pair(3))
    labels = ['Size', 'Entry Price', 'Unrealized PNL', 'Realized PNL']
    space = 0
    # scr.addstr(startY + 1, space, '_________________________________________________________________________________')
    for val in labels:
        scr.addstr(startY + 2, startX + space , '|')
        scr.addstr(startY + 2, startX + space + 10 - (len(val)//2), val, curses.A_UNDERLINE)
        space += 20
    scr.addstr(startY + 2, startX + space, '|')
    space = 0
    items = ['size', 'entry_price', 'unrealised_pnl', 'realised_pnl']
    for i, val in enumerate(items):
        scr.addstr(startY + 3, startX + space, '|')
        try:
            scr.addstr(startY + 3, startX + space + 10 - (len(str(pos[val]))//2), str(pos[val]))
        except Exception:
            pass
        space += 20
    # scr.addstr(startY + 4, 0, '_________________________________________________________________________________')
    scr.addstr(startY + 3, startX + space, '|')

prevBal = 00.00
def updateBalDisp(scr, q, btc):
    global prevAsk
    global prevBal
    y, x = scr.getmaxyx()
    info = None
    while not q.empty():
        info = q.get(False)
        prevBal = info['equity']
    if info is None: bal = prevBal
    else: bal = info['equity']
    msg = 'Balance: ₿'
    scr.addstr(1, x - x//4 + len(msg) + 1, '                 ')
    if btc:
        scr.addstr(1, x - x//4 + len(msg) + 1, str(bal))
    else:
        msg = 'Balance: $'
        dolBal = bal*float(prevAsk)
        dolBal = f"{dolBal:,}"
        split = dolBal.split('.')
        dolBal = split[0] + '.' + split[1][0:2]
        scr.addstr(1, x - x//4 + len(msg) + 1, dolBal)
    scr.addstr(1, x - x//4, msg)

def fixPrice(price):
    return price + '.00' if price[-2] != '.' else price + '0'

def getAmnt(msg, scr, qs, btc):
    scr.clear()
    y, x = scr.getmaxyx()
    scr.addstr(y//2 - 3,x//2 - (len(msg)//2),msg)
    box = curses.newwin(3, 50, y // 2 - 2, x // 2 - 25)
    box.border()
    scr.refresh()
    box.refresh()
    amnt = ''
    spot = x // 2 - 22
    scr.addstr(y // 2 - 1, spot - 1, '$')
    runUpdaters(scr, qs, btc)
    while 1:
        key = scr.getch()
        if key == -1: continue
        val = chr(key)
        runUpdaters(scr, qs, btc)
        if key == 10:
            return float(amnt)
        elif key == 263 and len(amnt) != 0:
            amnt = amnt[:-1]
            scr.addstr(y // 2 - 1, spot - 2, ' ')
            rewriteNum(scr, amnt, x, y)
            spot -= 1
            if len(amnt) % 3 == 0:
                scr.addstr(y // 2 - 1, spot - 2, ' ')
                spot -= 1
        elif val.isnumeric() or val == '.':
            amnt += val
            rewriteNum(scr, amnt, x, y)
            if (len(amnt) - 1) % 3 == 0: spot += 1
            spot += 1
        elif val == 's':
            scr.clear()
            return -1
        time.sleep(.01)

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
    h, w = scr.getmaxyx()
    y = h//2
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
    for i, val in enumerate(menuItems):
        x = w//2 - (10 * ((len(menuItems)//2) - i)) - (len(val)//2)
        if col == i:
            scr.attron(curses.color_pair(1))
            scr.addstr(y,x,val)
            scr.attroff(curses.color_pair(1))
        else:
            scr.addstr(y,x,val)
    scr.refresh()

def initColors():
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)

def loadConfig():
    confFile = json.load(open('./config.json', 'r'))
    return confFile['key'], confFile['secret']

def printt(txt):
    file = open('./text.txt', 'a')
    file.write(str(txt) + '\n')
    file.close()

if __name__ == '__main__':
    curses.wrapper(main)
