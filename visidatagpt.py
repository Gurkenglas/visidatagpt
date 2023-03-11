import curses, sys, varname
from lenses import lens, bind
import regex as re

relens = lambda self: lens.Lens(lambda s: self.search(s).group(0), lambda old, new: self.sub(new, old))

optics = bind(open("optics.json").read()).Json().Each().F(lambda d: d.values()).Parts() #bootstrap
def plumb(s, t):
    for os, ot, o in optics.get():
        if s == os:
            if t == ot: return eval(o)
            ott = plumb(ot, t)
            if ott: return eval(o) & ott

def sheet():
    return bind(f"{varname.varname()}.json") & plumb("file","lists")
optics = sheet()
help = sheet()

@curses.wrapper
def main(window : curses.window):
    rc = bind(window) & plumb("window", "rc")
    sheets = [optics, help]
    commandlog = []
    while True:
        r,c = rc.get()
        rows = sheets[-1].get()
        for rindex, row in enumerate(rows):
            for cindex, cell in enumerate(row):
                window.addstr(*plumb("yx","rc").flip().get()((rindex,cindex)), str(cell))
        rc.set((r,c))
        cell = sheets[-1][r][c]
        value = cell.get()
        key = window.getkey()
        for cmd in help.get():
            if cmd[0] == key:
                eval(cmd[2])
                commandlog.append(cmd)
                break