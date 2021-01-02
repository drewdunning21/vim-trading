from .winClass import winClass
from typing import Any

class menuWindow(winClass):

    def __init__(self, scr: Any, h: int, w: int, y: int, x: int, items: list, sel: int):
        winClass.__init__(self, scr, h, w, y, x)
        self.bal: int = 0
        self.items: list = items
        self.selected: int = sel
        self.makeMenu(sel, True)

    def makeMenu(self, newSel: int, force: bool):
        if newSel == self.selected and not force: return
        elif newSel >= len(self.items) or newSel < 0: return
        else: self.selected = newSel
        y, x = self.scr.getmaxyx()
        startX:int = x//2 - 10* (len(self.items)//2)
        if len(self.items)%2 != 0: startX -= 5
        for i, val in enumerate(self.items):
            if self.selected == i: self.addstr(1, (startX + (i * 10)) + (5 - (len(val)//2)), val, 0, stand=True)
            else: self.addstr(1, (startX + (i * 10)) + (5 - (len(val)//2)), val, 0)
        self.win.noutrefresh()

    ''' GETTERS '''

    def getSel(self) -> int:
        return self.selected

    ''' SETTERS '''

    def setMenu(self, items: list, sel: int):
        self.items = items
        self.selected = sel
        self.makeMenu(sel, True)
