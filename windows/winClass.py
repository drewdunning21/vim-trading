import curses

class winClass:

    def __init__(self, scr, h, w, y, x):
        self.scr = scr
        self.h, self.w, self.y, self.x = h, w, y, x
        self.win = self.makeWin()

    def makeWin(self):
        win = self.scr.subwin(self.h, self.w, self.y, self.x)
        return win

    def addstr(self, y: int, x: int, msg: str, color: int, under: bool = False, bold: bool = False, stand: bool = False):
        attrs = curses.color_pair(color)
        if bold: attrs += curses.A_BOLD
        if under: attrs += curses.A_UNDERLINE
        if stand: attrs += curses.A_STANDOUT
        self.win.addstr(y, x, msg, attrs)

    def switchSign(self):
        pass
