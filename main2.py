import curses, math, time, json
from BybitAcct import BybitAcct
from windows.priceWindow import priceWindow
from windows.posWindow import posWindow
from windows.balWindow import balWindow
from windows.menuWindow import menuWindow
from windows.winClass import winClass
from typing import Any

def main(scr: Any) -> None:
    initColors()
    conf: dict  = loadConfig()
    client: BybitAcct = connect(scr, conf)
    scr.nodelay(1)
    wins: dict[str, winClass] = getWins(scr)
    y, x = scr.getmaxyx()
    menu: menuWindow = menuWindow(scr, 3, x, y//2-1, 0, ['Buy', 'Sell'], 0)
    while 1:
        key: int = scr.getch()
        runUpdaters(wins)
        scr.refresh()
        if key == -1: continue
        val = chr(key)
        # left
        if val == 'm':
            menu.makeMenu(menu.getSel() - 1, False)
        # right
        elif val == 'i':
            menu.makeMenu(menu.getSel() + 1, False)
        # changs currency display
        elif val == 'd':
            wins['balWin'].switchSign()
            wins['posWin'].switchSign()
        # settings page
        elif val == 'a':
            scr.erase()
            settingsPage(scr, conf)
            menu.makeMenu(menu.getSel(), True)
            scr.refresh()
        # select
        elif val == 't' or key == 10:
            menu.win.erase()
            orderPage(scr, wins, menu, client, conf)
            scr.erase()
            menu.setMenu(['Buy', 'Sell'], 0)
            scr.refresh()
        elif val == 'h' or key == 10:
            histPage(scr)
        # exit the program
        elif val == 'q': break
        time.sleep(.01)

''' PAGES '''

def orderPage(scr: Any, wins: dict, menu: menuWindow, client: BybitAcct, conf: dict) -> None:
    if menu.getSel() == 0: side: str = 'Buy'
    else: side: str = 'Sell'
    menu.setMenu(['Market', 'Limit', 'Chase'], 1)
    while 1:
        key: int = scr.getch()
        runUpdaters(wins)
        scr.refresh()
        if key == -1: continue
        val: str = chr(key)
        if val == 's':
            menu.win.erase()
            menu.setMenu(['Buy', 'Sell'], 0)
            return
        if val == 'm':
            menu.makeMenu(menu.getSel() - 1, False)
        if val == 'i':
            menu.makeMenu(menu.getSel() + 1, False)
        if val == 'd':
            wins['balWin'].switchSign()
            wins['posWin'].switchSign()
        if val == 't' or key == 10:
            sel: int = menu.getSel()
            if sel == 0: marketOrder(scr, client, side, conf, wins)
            if sel == 1: limitOrder(scr, client, side, conf, wins)
            if sel == 2: chaseOrder(scr, client, side, conf, wins)
            return
        time.sleep(.01)

# settings page
def settingsPage(scr: Any, conf: dict) -> dict:
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

# history page
def histPage(scr: Any):
    pass

''' ORDERS '''

# market order
def marketOrder(scr: Any, client: BybitAcct, side: str,  conf: dict, wins: dict) -> bool:
    runUpdaters(wins)
    auto = conf['autosize']
    # get the stop loss
    sl = getAmnt('Enter stop-loss ($)', scr, wins)
    if sl == -1: return False
    # gets the trades size
    if auto: amnt = getSize(conf, sl, wins['priceWin'].getAsk(), wins)
    else: amnt = getAmnt('Enter size ($)', scr, wins)
    amnt = int(str(amnt).split('.')[0])
    if amnt == -1: return False
    client.marketOrder('BTCUSD', amnt, side)
    return True

# limit order
def limitOrder(scr: Any, client: BybitAcct, side: str, conf: dict, wins: dict) -> bool:
    # get trade price
    price = getAmnt('Enter price ($)', scr, wins)
    if price == -1: return False
    # get the stop loss
    sl = getAmnt('Enter stop-loss ($)', scr, wins)
    if sl == -1: return False
    # get trade size
    auto = conf['autosize']
    if auto: amnt = getSize(conf, sl, wins['priceWin'].getAsk(), wins)
    else: amnt = getAmnt('Enter size ($)', scr, wins)
    amnt = int(str(amnt).split('.')[0])
    if amnt == -1: return False
    # make the trade
    client.limitOrder('BTCUSD', amnt, price, side)
    return True

# chase order
def chaseOrder(scr: Any, client: BybitAcct, side: str, conf: dict, wins: dict) -> bool:
    # get the stop loss
    sl = getAmnt('Enter stop-loss ($)', scr, wins)
    if sl == -1: return False
    # get the take profit
    tp = getAmnt('Enter stop-loss ($)', scr, wins)
    if tp == -1: return False
    # get trade size
    auto = conf['autosize']
    if auto: amnt = getSize(conf, sl, wins['priceWin'].getAsk(), wins)
    else: amnt = getAmnt('Enter size ($)', scr, wins)
    amnt = int(str(amnt).split('.')[0])
    if amnt == -1: return False
    if side == 'Buy':   chaseBuy(client, 'BTCUSD', amnt, scr, wins, conf, sl, tp)
    else:               chaseSell(client, 'BTCUSD', amnt, scr, wins, conf, sl, tp)
    return True

# chase buy
def chaseBuy(client: BybitAcct, symbol: str, amnt: int, scr, wins: dict, conf: dict, sl, tp, maxPrice=100000000):
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
        runUpdaters(wins)
        spread = client.getSpread(symbol)
        newBid = float(spread['bid']['price'])
        # check if price greater than max price
        if newBid > maxPrice:
            return 0
        # if not, check if the cur bid is greater than cur order bid
        if newBid != bid:
            # if so, adjust cur order bid
            if conf['auto']: amnt = int(str(getSize(conf, sl, wins['priceWin'].getAsk(), wins)).split('.')[0])
            orderId = client.replaceOrder(orderId, symbol, str(newBid), str(amnt))
            bid = newBid
        orderStatus = client.getStatus(symbol, orderId)
        status = orderStatus['order_status']
        orderStatusPage(scr, orderStatus['cum_exec_qty'], orderStatus['qty'])
    return orderId

# chase sell
def chaseSell(client: BybitAcct, symbol: str, amnt: int, scr, wins: dict, conf: dict, sl, tp, minPrice=0):
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
        runUpdaters(wins)
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

''' UTILITY '''

def runUpdaters(wins: dict) -> None:
    for val in wins.values():
        val.updateDisp()

# gets a number amount as input from the user
def getAmnt(msg: str, scr: Any, wins: dict) -> float:
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
    runUpdaters(wins)
    while 1:
        key = scr.getch()
        if key == -1: continue
        val = chr(key)
        runUpdaters(wins)
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
def getPcnt(msg: str, scr: Any) -> float:
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

# auto calcs position size based off risk parameters
def getSize(conf: dict, sl: float, price: str, wins: dict) -> float:
    risk = conf['risk'] / 100
    fPrice = float(price)
    gap = fPrice - sl
    lev = 0
    # long
    if gap > 0:
        actRisk = gap / fPrice
        lev = risk / actRisk
    # short
    else:
        actRisk = (sl / fPrice) - 1
        lev = risk / actRisk
    return lev * float(wins['balWin'].getBal()) * fPrice

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

def addstr(scr, y: int, x: int, msg: str, color: int, under: bool = False, bold: bool = False, stand: bool = False):
    attrs = curses.color_pair(color)
    if bold: attrs += curses.A_BOLD
    if under: attrs += curses.A_UNDERLINE
    if stand: attrs += curses.A_STANDOUT
    scr.addstr(y, x, msg, attrs)

''' INITIALIZE FUCTIONS '''

# gets the dictionary of windows
def getWins(scr: Any) -> dict:
    x: int = 0
    y: int = 0
    y, x = scr.getmaxyx()
    wins: dict = {}
    wins['priceWin'] = priceWindow(scr, 3, 40, y//4, x//2-20)
    wins['posWin'] = posWindow(scr, 4, 80, y - (y//4), x//2-40, wins['priceWin'])
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
    quit()
