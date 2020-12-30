from .winClass import winClass
from updaters.priceUpdater import getPrices
from multiprocessing import Process, Queue
from typing import Any

class priceWindow(winClass):

    def __init__(self, scr: Any, h: int, w: int, y: int, x: int):
        winClass.__init__(self, scr, h, w, y, x)
        self.bid: str = '-'
        self.ask: str = '-'
        self.last: str = '-'
        self.p, self.q = self.getPQ()
        self.win.refresh()

    ''' DISPLAY UPDATER '''

    def updateDisp(self):
        ran = False
        while not self.q.empty():
            self.bid, self.ask = self.fixPrice(self.q.get(False))
            ran = True
        if ran: return
        self.win.erase()
        y, x = self.win.getmaxyx()
        # displays the bid
        self.addstr(1, x//2 - (10 + len(self.bid)//2), self.bid, 2)
        # displays the ask
        self.addstr(1, x//2 + (10 - len(self.ask)//2), self.ask, 1)
        self.win.box()
        self.win.refresh()
        # self.scr.refresh()

    def getPQ(self):
        q = Queue()
        p = Process(target=getPrices, args=(q, 1))
        p.start()
        return p, q

    ''' GETTERS '''

    def getBid(self):
        return self.bid

    def getAsk(self):
        return self.ask

    def getLast(self):
        return self.last

    ''' UTILITIES '''

    def fixPrice(self, prices: tuple) -> tuple:
        bid, ask = prices
        return (bid + '.00' if bid[-2] != '.' else bid + '0', ask + '.00' if ask[-2] != '.' else ask + '0')
