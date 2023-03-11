import curses
import sys
from lenses import lens, bind
import regex as re
from typing import List, Generic
import varname
import json

relens = lambda self: lens.Lens(lambda s: self.search(s).groups(), lambda old, new: self.sub(new, old))

class CodeSheet(List[dict]):
    def __init__(self, dicts):
        super().__init__(dicts)
        self.name = varname.varname()
    sheet = lambda self: bind(__file__) & plumb("file","str") & relens(re.compile(self.name + r" = CodeSheet\((\[.*\])\)", re.DOTALL))[0] & plumb("str","lists")

optics = CodeSheet([
    {"s":"file"  ,"t":"str"  ,"o":"lens.Lens(lambda filename: open(filename).read(), lambda filename, new: open(filename, 'w').write(new))"},
    {"s":"str"   ,"t":"dicts","o":"lens.Iso(json.loads, json.dumps)"},
    {"s":"dicts" ,"t":"lists","o":"lens.Iso(lambda dicts: [list(dicts[0].keys())] + [list(row.values()) for row in dicts], lambda lists: [dict(zip(lists[0], row)) for row in lists][1:])"},
    {"s":"yx"    ,"t":"rc"   ,"o":"lens.Iso(lambda yx: (yx[0], yx[1]//10), lambda yx: (yx[0], yx[1]*10))"},
    {"s":"window","t":"yx"   ,"o":"lens.Lens(lambda w: w.getyx(),lambda w,yx: w.move(*yx))"}
])

def plumb(s, t):
    for d in optics:
        o, os, ot = d["o"], d["s"], d["t"]
        if s == os:
            if t == ot: return eval(o)
            ott = plumb(ot, t)
            if ott: return eval(o) & ott

def main(stdscr : curses.window):
    rc = bind(stdscr) & plumb("window", "rc")
    sheets = [optics.sheet()]
    commandlog = []
    while True:
        r,c = rc.get()
        stdscr.clear()
        rows = sheets[-1].get()
        for rindex, row in enumerate(rows):
            for cindex, cell in enumerate(row):
                stdscr.addstr(*plumb("yx","rc").flip().get()((rindex,cindex)), str(cell))
        rc.set((r,c))
        cell = sheets[-1][r][c]
        value = cell.get()
        help = [
            {"key": "KEY_UP"   ,"desc": "go up"       ,"do":lambda:rc[0]-1                                  ,"undo":lambda: rc[0]+1},
            {"key": "KEY_DOWN" ,"desc": "go down"     ,"do":lambda:rc[0]+1                                  ,"undo":lambda: rc[0]-1},
            {"key": "KEY_RIGHT","desc": "go right"    ,"do":lambda:rc[1]+1                                  ,"undo":lambda: rc[1]-1},
            {"key": "KEY_LEFT" ,"desc": "go left"     ,"do":lambda:rc[1]-1                                  ,"undo":lambda: rc[1]+1},
            {"key": "d"        ,"desc": "flush cell"  ,"do":lambda:cell.set("")                             ,"undo":lambda: cell.set(value)},
            {"key": "q"        ,"desc": "quit"        ,"do":lambda:sys.exit(0)                              ,"undo":lambda: print("Panic!")},
            {"key": "H"        ,"desc": "help"        ,"do":lambda:openkeymap()                             ,"undo":lambda: closekeymap()},
            {"key": "U"        ,"desc": "undo history","do":lambda:opencommands()                           ,"undo":lambda: closehelp},
            {"key": "e"        ,"desc": "edit cell"   ,"do":lambda:cell.set(stdscr.getstr().decode("utf-8")),"undo":lambda: cell.set(value)},
        ]
        key = stdscr.getkey()
        for cmd in help:
            if cmd["key"] == key:
                cmd["do"]()
                commandlog.append(cmd)
                break

if __name__ == "__main__":
    curses.wrapper(main)