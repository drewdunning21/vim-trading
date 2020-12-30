from .winClass import winClass
from updaters.posUpdater import getPos
from multiprocessing import Process, Queue
from typing import Any

class posWindow(winClass):

    def __init__(self, scr, h: int, w: int, y: int, x: int):
        winClass.__init__(self, scr, h, w, y, x)
        self.pos: dict = {}
        self.RPnl: int = 0
        self.UPnl: int = 0
        self.size: int = 0
        self.entry: int = 0
        self.p, self.q = self.getPQ()
        self.win.refresh()

    ''' DISPLAY UPDATER '''

    def updateDisp(self):
        newPos = None
        while not self.q.empty():
            newPos = self.q.get(False)
        if newPos != None: self.pos = newPos
        # if pos is None: pos = prevPos
        y, x = self.win.getmaxyx()
        startY, startX = 0,0
        # startY, startX = math.floor(y * .7), math.floor(x * .01)
        # self.addstr(startY, startX, 'Positions', 0, bold=True)
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
                self.addstr(startY + 2, startX + space + 10 - (len(str(self.pos[val]))//2), str(self.pos[val]), 0)
            except Exception:
                pass
            space += 20
        self.win.box()
        self.win.refresh()

    def getPQ(self):
        q = Queue()
        p = Process(target=getPos, args=(q, 1))
        p.start()
        return p, q

    ''' GETTERS '''

    def getRPnl(self):
        return self.RPnl

    def getUPnl(self):
        return self.UPnl

    def getEntry(self):
        return self.entry

    def getSize(self):
        return self.size
