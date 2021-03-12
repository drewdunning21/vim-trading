from .winClass import winClass
from updaters.balUpdater import getBal
from multiprocessing import Process, Queue
from .priceWindow import priceWindow
from typing import Any

class balWindow(winClass):

    def __init__(self, scr: Any, h: int, w: int, y: int, x: int, priceWin: priceWindow):
        winClass.__init__(self, scr, h, w, y, x)
        self.bal: int = 0
        self.priceWin: priceWindow = priceWin
        self.btc: bool = True
        self.info: dict = {'equity': 0}
        self.p, self.q = self.getPQ()

    ''' DISPLAY UPDATER '''

    def updateDisp(self):
        y, x = self.win.getmaxyx()
        newInfo = None
        while not self.q.empty():
            newInfo = self.q.get(False)
        self.win.erase()
        if newInfo is not None: self.info = newInfo
        printt(self.info)
        self.bal = self.info['equity']
        msg: str = 'Balance: ₿'
        self.win.addstr(1, 1, '                 ')
        if self.btc:
            self.addstr(1, len(msg) + 2, str(self.bal), 0)
        else:
            prevAsk: str = self.priceWin.getAsk()
            if prevAsk == '-': return
            msg = 'Balance: $'
            dolBal = self.bal*float(prevAsk)
            dolBal = f"{dolBal:,}"
            split = dolBal.split('.')
            dolBal = split[0] + '.' + split[1][0:2]
            self.addstr(1, 1 + len(msg), dolBal, 0)
        self.win.addstr(1, 1, msg)
        self.win.noutrefresh()

    def switchSign(self):
        self.btc = not self.btc

    def getPQ(self):
        q = Queue()
        p = Process(target=getBal, args=(q, 1))
        p.start()
        return p, q

    ''' GETTERS '''

    def getBal(self):
        return self.bal

    def getBtc(self):
        return self.btc

    def getInfo(self):
        return self.info


def printt(txt):
    file = open('./text.txt', 'a')
    file.write(str(txt) + '\n')
    file.close()
