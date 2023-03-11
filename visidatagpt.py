import curses
import sys
from lenses.ui import BoundLens, UnboundLens
from lenses import lens, bind
import re
from typing import List
import varname
import json
import inspect

def regex(s : str, *args, **kwargs) -> UnboundLens[str, str, str, str]:
    r = re.compile(s)
    return lens.Lens(lambda string: r.search(string, *args, **kwargs).group(), lambda old, new: r.sub(new, old, *args, **kwargs))
filetostring  = lens.Lens(lambda filename: open(filename).read(), lambda filename, new: open(filename, "w").write(new))
stringtodicts = lens.Iso(json.loads, json.dumps)
dictstolists  = lens.Iso(lambda dicts: [list(dicts[0].keys())] + [list(row.values()) for row in dicts], lambda lists: [dict(zip(lists[0], row)) for row in lists][1:])
yxtorc        = lens.Iso(lambda yx: (yx[0], yx[1]//10), lambda yx: (yx[0], yx[1]*10))

class CodeSheet(List[dict]):
    def __init__(self, dicts):
        name = varname.varname()
        self.dicts = dicts
        filetojson = bind(__file__) & filetostring & regex(name + r" = CodeSheet\((\[.*\])\)", re.DOTALL) & stringtodicts
        self.sheet = filetojson & dictstolists

def optic(**kwargs):
    o = (lens.Lens if len(inspect.signature(kwargs["backward"]).parameters) == 2 else lens.Iso)(kwargs["forward"], kwargs["backward"])
    for k,v in kwargs.items():
        setattr(o, k, v)
    return o

optics = CodeSheet([
    {"source":"file","target":"string","forward":lambda filename: open(filename).read(),"backward":lambda filename, new: open(filename, "w").write(new)},
    {"source":"string","target":"dicts","forward":json.loads, "backward":json.dumps},
    {"source":"dicts","target":"lists","forward":lambda dicts: [list(dicts[0].keys())] + [list(row.values()) for row in dicts], "backward":lambda lists: [dict(zip(lists[0], row)) for row in lists][1:]},
    {"source":"yx","target":"rc","forward":lambda yx: (yx[0], yx[1]//10), "backward":lambda yx: (yx[0], yx[1]*10)},
])

def main(stdscr : curses.window):
    rc = bind(stdscr).Lens(lambda w: w.getyx(),lambda w,yx: w.move(*yx)) & yxtorc
    sheets = [bind(sys.argv[1]) & filetostring & stringtodicts & dictstolists]
    commandlog = []
    while True:
        r,c = rc.get()
        stdscr.clear()
        rows = sheets[-1].get()
        for rindex, row in enumerate(rows):
            for cindex, cell in enumerate(row):
                stdscr.addstr(*yxtorc.flip().get()((rindex,cindex)), str(cell))
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