from .winClass import winClass
from updaters.posUpdater import getPos
from multiprocessing import Process, Queue
from typing import Any
from .priceWindow import priceWindow

class posWindow(winClass):

    def __init__(self, scr: Any, h: int, w: int, y: int, x: int, priceWin: priceWindow):
        winClass.__init__(self, scr, h, w, y, x)
        self.pos: dict = {}
        self.RPnl: int = 0
        self.UPnl: int = 0
        self.size: int = 0
        self.entry: int = 0
        self.btc = True
        self.priceWin: priceWindow = priceWin
        self.setPQ()

    ''' DISPLAY UPDATER '''

    def updateDisp(self):
        newPos = None
        while not self.q.empty():
            newPos = self.q.get(False)
        if newPos != None: self.pos = newPos
        self.win.erase()
        startY, startX = 0,0
        labels: list = ['Size', 'Entry Price', 'Unrealized PNL', 'Realized PNL']
        space = 0
        for val in labels:
            self.addstr(startY + 1, startX + space , '|', 0)
            self.addstr(startY + 1, startX + space + 10 - (len(val)//2), val, 0, under = True)
            space += 20
        space = 0
        items = ['size', 'entry_price', 'unrealised_pnl', 'realised_pnl']
        for val in items:
            self.addstr(startY + 2, startX + space, '|', 0)
            try:
                if 'pnl' in val:
                    if not self.btc:
                        self.pos[val] = float(self.pos[val]) * float(self.priceWin.getAsk())
                        self.addstr(startY + 2, startX + space + 10 - (len(str(self.pos[val]))//2), '$' + str(self.pos[val]), 0)
                    else:
                        self.addstr(startY + 2, startX + space + 10 - (len(str(self.pos[val]))//2), str(self.pos[val]), 0)
                else:
                    self.addstr(startY + 2, startX + space + 10 - (len(str(self.pos[val]))//2), str(self.pos[val]), 0)
            except Exception:
                pass
            space += 20
        self.win.box()
        self.win.noutrefresh()

    def setPQ(self):
        self.q = Queue()
        self.p = Process(target=getPos, args=(self.q, 1))
        self.p.start()

    def switchSign(self):
        self.btc = not self.btc

    ''' GETTERS '''

    def getRPnl(self):
        return self.RPnl

    def getUPnl(self):
        return self.UPnl

    def getEntry(self):
        return self.entry

    def getSize(self):
        return self.size
