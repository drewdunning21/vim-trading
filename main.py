import curses, math, time, json
from BybitAcct import BybitAcct
from multiprocessing import Process, Queue
from priceUpdater import getPrices
from posUpdater import getPos
from balUpdater import getBal
from chart import updateChart

def main(scr):
    conf = loadConfig()
    client = connect(scr, conf)
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
        if key == curses.KEY_RESIZE: scr.clear()
        if key == ord('m') and col != 0:
            # left
            col -= 1
        elif key == ord('i') and col != len(menuItems) - 1:
            # right
            col += 1
        elif key == 10 or key == ord('t'):
            scr.clear()
            orderPage(scr, col, client, qs, btc, conf)
        elif key == ord('d'):
            btc = not btc
        elif key == ord('a'):
            scr.clear()
            conf = settingsPage(scr, conf)
        elif key == ord('c'):
            startChartUpdater('60')
            scr.clear()
            chartPage(scr)
        elif key == ord('q'):
            exit()
        hMenu(scr, col, menuItems)
        scr.refresh()
        time.sleep(.01)

''' PAGES '''

# order page
def orderPage(scr, order: int, client: BybitAcct, qs: list, btc: bool, conf: dict):
    runUpdaters(scr, qs, btc)
    menuItems = ['Market', 'Limit', 'Chase']
    col = 1
    side = 'Buy' if order == 0 else 'Sell'
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
            if col == 0:    order = marketOrder(scr, client, side, qs, btc, conf)
            elif col == 1:  order = limitOrder(scr, client, side, qs, btc, conf)
            else:           order = chaseOrder(scr, client, side, qs, btc, conf)
            if order:
                scr.clear()
                return
        elif key == ord('s'):
            scr.clear()
            return
        time.sleep(.01)

# settings page
def settingsPage(scr, conf: dict) -> dict:
    row: int = 0
    initSettings(scr, conf, row)
    while 1:
        stop: bool = conf['autosize']
        key = scr.getch()
        if key == -1: pass
        elif key == ord('s'):
            saveConfig(conf)
            scr.clear()
            return conf
        elif key == ord('m') and not stop and row==0:
            stop = conf['autosize'] = not stop
            initSettings(scr, conf, row)
        elif key == ord('i') and stop and row==0:
            stop = conf['autosize'] = not stop
            initSettings(scr, conf, row)
        elif key == ord('n') and row != 2:
            row += 1
            initSettings(scr, conf, row)
        elif key == ord('e') and row != 0:
            row -= 1
            initSettings(scr, conf, row)
        elif (key == ord('t') or key == 10) and row == 1:
            pcnt: float = getPcnt('Enter Risk Percent', scr)
            scr.clear()
            conf['risk'] = pcnt
            initSettings(scr, conf, row)
        elif (key == ord('t') or key == 10) and row == 2:
            saveConfig(conf)
            scr.clear()
            return conf
        time.sleep(.01)
    return conf

def initSettings(scr, conf: dict, row: int) -> None:
    y, x = scr.getmaxyx()
    setStr: str = 'Settings'
    addstr(scr, y//4,x//2 - len(setStr)//2, setStr, 0, bold=True)
    stop: bool = conf['autosize']
    risk: int = conf['risk']
    # auto stop
    startY = y//4
    addstr(scr, startY + 5, x//2 - len('Autosize: Yes No')//2, 'Autosize:', 0, stand=(row==0))
    yes, no = False, True
    if stop: yes, no = no, yes
    addstr(scr, startY + 5, x//2 + 3, 'Yes', 0, under=yes)
    addstr(scr, startY + 5, x//2 + 7, 'No', 0, under=no)
    # risk amount (%)
    addstr(scr, startY + 10, x//2 - (len('Risk (%): ' + str(risk) + 'Edit') + 2)//2, 'Risk (%):', 0, stand=(row==1))
    yes, no = False, True
    if stop: yes, no = no, yes
    addstr(scr, startY + 10, x//2 + 3, str(risk) + '%', 0, under=False)
    addstr(scr, startY + 10, x//2 + 3 + len(str(risk)) + 2, 'Edit', 0, under=True)
    # save button
    addstr(scr, startY + 15, x//2 - len('Save')//2, 'Save', 0,  stand=(row==2))
    scr.refresh()

def chartPage(scr):
    scr.clear()
    key = -1
    while key != ord('s'):
        y, x = scr.getmaxyx()
        addstr(scr, y//4, x//2 - len('Chart Settings')//2, 'Chart Settings', 0)
        key = scr.getch()
        if key == curses.KEY_RESIZE: scr.clear()
    scr.clear()
    return

''' ORDERS '''

# market order
def marketOrder(scr, client: BybitAcct, side: str, qs: list, btc: bool, conf: dict) -> bool:
    global prevAsk
    runUpdaters(scr, qs, btc)
    auto = conf['autosize']
    # get the stop loss
    sl = getAmnt('Enter stop-loss ($)', scr, qs, btc)
    if sl == -1: return False
    # gets the trades size
    if auto: amnt = getSize(conf, sl, prevAsk)
    else: amnt = getAmnt('Enter size ($)', scr, qs, btc)
    amnt = int(str(amnt).split('.')[0])
    if amnt == -1: return False
    printt('amnt ' + str(amnt))
    # client.marketOrder('BTCUSD', amnt, side)
    return True

# limit order
def limitOrder(scr, client: BybitAcct, side: str, qs: list, btc: bool, conf: dict) -> bool:
    # get trade price
    price = getAmnt('Enter price ($)', scr, qs, btc)
    if price == -1: return False
    # get the stop loss
    sl = getAmnt('Enter stop-loss ($)', scr, qs, btc)
    if sl == -1: return False
    # get trade size
    auto = conf['autosize']
    if auto: amnt = getSize(conf, sl, price=price)
    else: amnt = getAmnt('Enter size ($)', scr, qs, btc)
    amnt = int(str(amnt).split('.')[0])
    if amnt == -1: return False
    # make the trade
    client.limitOrder('BTCUSD', amnt, price, side)
    return True

# chase order
def chaseOrder(scr, client: BybitAcct, side: str, qs: list, btc: bool, conf: dict) -> bool:
    global prevAsk
    # get the stop loss
    sl = getAmnt('Enter stop-loss ($)', scr, qs, btc)
    if sl == -1: return False
    # get trade size
    auto = conf['autosize']
    if auto: amnt = getSize(conf, sl, prevAsk)
    else: amnt = getAmnt('Enter size ($)', scr, qs, btc)
    amnt = int(str(amnt).split('.')[0])
    if amnt == -1: return False
    if side == 'Buy':   chaseBuy(client, 'BTCUSD', amnt, qs, scr, btc)
    else:               chaseSell(client, 'BTCUSD', amnt, qs, scr, btc)
    return True

# chase buy
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

# chase sell
def chaseSell(client: BybitAcct, symbol: str, amnt: int, qs: list, scr, btc: bool, minPrice=0):
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

''' UPDATERS '''

# starts the updaters
def startUpdaters():
    uP, uQ = startPriceUpdater()
    pP, pQ = startPosUpdater()
    bP, bQ = startBalUpdater()
    return [uP, pP, bP], [uQ, pQ, bQ]

# starts price updater
def startPriceUpdater():
    q = Queue()
    p = Process(target=getPrices, args=(q, 1))
    p.start()
    return p, q

# starts position updater
def startPosUpdater():
    q = Queue()
    p = Process(target=getPos, args=(q, 1))
    p.start()
    return p, q

# starts balance updater
def startBalUpdater():
    q = Queue()
    p = Process(target=getBal, args=(q, 1))
    p.start()
    return p, q

# starts the chart updater
chartStarted = False
def startChartUpdater(timeP):
    global chartStarted
    if chartStarted: return
    chartStarted = not chartStarted
    q = Queue()
    p = Process(target=updateChart, args=(q, timeP))
    p.start()
    return p, q

# runs all the updaters
def runUpdaters(scr, qs, btc):
    updatePriceDisp(scr, qs[0])
    updatePosDisp(scr, qs[1])
    updateBalDisp(scr, qs[2], btc)

# updates the price in the center middle
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
    addstr(scr, y//4, x//2 - 5 - len(bid), bid, 2)
    # displays the ask
    addstr(scr, y//4, x//2 + 5, ask, 1)
    scr.refresh()

# updates the position display
prevPos = {}
def updatePosDisp(scr, q):
    global prevPos
    pos = None
    while not q.empty():
        pos = q.get(False)
        prevPos = pos
    if pos is None: pos = prevPos
    y, x = scr.getmaxyx()
    startY, startX = math.floor(y * .7), x//2 - 40,
    # startY, startX = math.floor(y * .7), math.floor(x * .01)
    addstr(scr, startY, startX, 'Positions', 0, bold=True)
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
    for val in items:
        scr.addstr(startY + 3, startX + space, '|')
        try:
            scr.addstr(startY + 3, startX + space + 10 - (len(str(pos[val]))//2), str(pos[val]))
        except Exception:
            pass
        space += 20
    # scr.addstr(startY + 4, 0, '_________________________________________________________________________________')
    scr.addstr(startY + 3, startX + space, '|')

# updates the balance display
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

''' UTILITY FUNCTIONS '''

# adds a 00 or 0 to the price depending on current format
def fixPrice(price):
    return price + '.00' if price[-2] != '.' else price + '0'

# auto calcs position size based off risk parameters
def getSize(conf, sl, price):
    global prevBal
    risk = conf['risk'] / 100
    price = float(price)
    gap = price - sl
    lev = 0
    # long
    if gap > 0:
        actRisk = gap / price
        lev = risk / actRisk
    # short
    else:
        actRisk = (sl / price) - 1
        lev = risk / actRisk
    return lev * prevBal * price

# gets a number amount as input from the user
def getAmnt(msg, scr, qs, btc) -> float:
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
    return float(amnt)

# gets a percent input from the user
def getPcnt(msg, scr) -> float:
    scr.clear()
    y, x = scr.getmaxyx()
    scr.addstr(y//2 - 3,x//2 - (len(msg)//2),msg)
    box = curses.newwin(3, 16, y // 2 - 2, x // 2 - 8)
    box.border()
    scr.refresh()
    box.refresh()
    amnt = ''
    spot = x // 2 + 1
    scr.addstr(y // 2 - 1, x//2 + 5, '%')
    numCount: int = 0
    while 1:
        key = scr.getch()
        if key == -1: continue
        val = chr(key)
        if key == 10:
            return float(amnt)
        elif key == 263 and len(amnt) != 0:
            if amnt[-1].isnumeric(): numCount -= 1
            amnt = amnt[:-1]
            spot -= 1
            scr.addstr(y // 2 - 1, spot - 2, ' ')
        elif (val.isnumeric() or val == '.') and numCount < 2:
            if val.isnumeric(): numCount += 1
            amnt += val
            scr.addstr(y // 2 - 1, spot - 2, val)
            spot += 1
        elif val == 's':
            scr.clear()
            return -1
        time.sleep(.01)
    return float(amnt)

# rewrites the number on the screen
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

# puts a menu of items vertically
def vMenu(scr, row, menuItems):
    scr.clear()
    h, w = scr.getmaxyx()
    for i, val in enumerate(menuItems):
        x = w//2 - len(val)//2
        y = h//2 - len(menuItems) + i
        if row == i:
            addstr(scr, y, x, val, 1)
        else:
            scr.addstr(y,x,val)
    scr.refresh()

# calls even or odd horizontal menu func
def hMenu(scr, col, menuItems):
    if len(menuItems) % 2 != 0: oddMenu(scr, col, menuItems)
    else: evenMenu(scr, col, menuItems)

# puts a menu of items horizontally
def evenMenu(scr, col, menuItems):
    h, w = scr.getmaxyx()
    y = h//2
    x = w//2 - (10 * (len(menuItems)//2))
    for i, val in enumerate(menuItems):
        x += len(val) // 2 + 1
        if col == i:
            addstr(scr, y, x, val, 0, stand=True)
        else:
            addstr(scr, y, x, val, 0)
        x += 10
    scr.refresh()

# puts a menu of items horizontally
def oddMenu(scr, col, menuItems):
    # scr.clear()
    h, w = scr.getmaxyx()
    y = h//2
    for i, val in enumerate(menuItems):
        x = w//2 - (10 * ((len(menuItems)//2) - i)) - (len(val)//2)
        if col == i:
            addstr(scr, y, x, val, 0, stand=True)
        else:
            addstr(scr, y, x, val, 0)
    scr.refresh()

# adds a string to the screen with a specified color
def addstr(scr, y: int, x: int, msg: str, color: int, under: bool = False, bold: bool = False, stand: bool = False):
    attrs = curses.color_pair(color)
    if bold: attrs += curses.A_BOLD
    if under: attrs += curses.A_UNDERLINE
    if stand: attrs += curses.A_STANDOUT
    scr.addstr(y, x, msg, attrs)

# prints to the text file
def printt(txt):
    file = open('./text.txt', 'a')
    file.write(str(txt) + '\n')
    file.close()

''' INITIALIZE FUCTIONS '''

# connect to bybit
def connect(scr, conf):
    curses.curs_set(0)
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

# loads the config data
def loadConfig() -> dict:
    return json.load(open('./config.json', 'r'))

def saveConfig(conf: dict):
    with open('config.json', 'w') as fp:
        json.dump(conf, fp)

if __name__ == '__main__':
    curses.wrapper(main)
