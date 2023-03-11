import curses
import sys
from lenses.ui import BoundLens, UnboundLens
import lenses.optics as o
from typing import Callable, Generic, TypeVar, List
import json

S = TypeVar("S")
T = TypeVar("T")
A = TypeVar("A")
B = TypeVar("B")

def boundlens(get : Callable[[],A], set : Callable[[B],T]) -> BoundLens[None,T,A,B]:
    return BoundLens(None, o.Lens(lambda none: get(), lambda none, new: set(new)))

filetostring = lambda filename: boundlens(lambda: open(filename).read(), lambda new: open(filename, "w").write(new))
stringtojson = UnboundLens(o.Isomorphism(json.loads, json.dumps))
dividexbyten = UnboundLens(o.Isomorphism(lambda yx: (yx[0], yx[1] // 10), lambda yx: (yx[0], yx[1] * 10)))

def main(stdscr : curses.window):
    yx = boundlens(lambda: stdscr.getyx(),lambda yx: stdscr.move(*yx)) & dividexbyten
    filename = sys.argv[1]
    sheet = filetostring(filename) & stringtojson
    def render(what):
        pos = yx.get()
        stdscr.clear()
        dicts = what.get()
        #for x, col in enumerate(dicts[0]):
        #    stdscr.addstr(0, x*10, col)
        for y, row in enumerate(dicts):
            for x, cell in enumerate(row.values()):
                stdscr.addstr(y, x*10, str(cell))
        yx.set(pos)
    commandlog = []
    while True:
        render(sheet)
        y,x = yx.get()
        cell = sheet[y].Each().Parts()[x][1]
        value = cell.get()
        keymap = {
            "KEY_UP"   : {"desc": "go up"      , "do": lambda: yx[0]-1     , "undo": lambda: yx[0]+1},
            "KEY_DOWN" : {"desc": "go down"    , "do": lambda: yx[0]+1     , "undo": lambda: yx[0]-1},
            "KEY_RIGHT": {"desc": "go right"   , "do": lambda: yx[1]+1     , "undo": lambda: yx[1]-1},
            "KEY_LEFT" : {"desc": "go left"    , "do": lambda: yx[1]-1     , "undo": lambda: yx[1]+1},
            "d"        : {"desc": "flush cell" , "do": lambda: cell.set(""), "undo": lambda: cell.set(value)},
            "e"        : {"desc": "edit"       , "do": lambda: cell.set(stdscr.getstr().decode("utf-8")), "undo": lambda: cell.set(value)},
            "q"        : {"desc": "quit"       , "do": lambda: sys.exit(0)},
            #"k"        : {"desc": "keymap"     , "do": lambda: openkeymap(), "undo": lambda: closekeymap()}   ,
            #"c"        : {"desc": "commands"   , "do": lambda: opencommands()} ,
        }
        key = stdscr.getkey()
        if not key in keymap: continue
        cmd = keymap[key]
        commandlog.append(cmd)
        cmd["do"]()

if __name__ == "__main__":
    curses.wrapper(main)