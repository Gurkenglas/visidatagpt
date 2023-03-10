import curses
import sys
from lenses.ui import BoundLens, UnboundLens
import lenses.optics as o
import csv

def boundlens(get, set):
    return BoundLens(None, o.Lens(lambda none: get(), lambda none, new: set(new)))

dividexbyten = UnboundLens(o.Lens(lambda yx: (yx[0], yx[1] // 10), lambda old, yx: (yx[0], yx[1] * 10)))

def main(stdscr : curses.window):
    yx = boundlens(lambda: stdscr.getyx(),lambda yx: stdscr.move(*yx)) & dividexbyten
    filename = sys.argv[1]
    sheet = boundlens(lambda: list(csv.reader(open(filename))),lambda rows: csv.writer(open(filename, "w")).writerows(rows))
    def render(what):
        pos = yx.get()
        stdscr.clear()
        for y, row in enumerate(what.get()):
            for x, cell in enumerate(row):
                stdscr.addstr(y, x*10, cell)
        yx.set(pos)
    commandlog = []
    while True:
        render(sheet)
        y,x = yx.get()
        cell = sheet[y][x]
        value = cell.get()
        keymap = {
            "KEY_UP"   : {"desc": "go up"      , "do": lambda: yx[0]-1     , "undo": lambda: yx[0]+1},
            "KEY_DOWN" : {"desc": "go down"    , "do": lambda: yx[0]+1     , "undo": lambda: yx[0]-1},
            "KEY_RIGHT": {"desc": "go right"   , "do": lambda: yx[1]+1     , "undo": lambda: yx[1]-1},
            "KEY_LEFT" : {"desc": "go left"    , "do": lambda: yx[1]-1     , "undo": lambda: yx[1]+1},
            "d"        : {"desc": "flush cell" , "do": lambda: cell.set(""), "undo": lambda: cell.set(value)},
            "e"        : {"desc": "edit"       , "do": lambda: cell.set(stdscr.getstr()), "undo": lambda: cell.set(value)},
            "q"        : {"desc": "quit"       , "do": lambda: sys.exit(0)},
        }
        cmd = keymap[stdscr.getkey()]
        commandlog.append(cmd)
        cmd["do"]()

if __name__ == "__main__":
    curses.wrapper(main)