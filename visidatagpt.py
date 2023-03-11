import curses
import sys
from lenses.ui import BoundLens, UnboundLens
import lenses.optics as o
import re
from typing import Callable, Generic, TypeVar, List
import varname
import json
import inspect

S = TypeVar("S")
T = TypeVar("T")
A = TypeVar("A")
B = TypeVar("B")

def merge_optics_with_equal_foci(left, right):
    result = left.copy()
    def get(*args, **kwargs):
        l = left.get(*args, **kwargs)
        r = right.get(*args, **kwargs)
        assert l == r, f"{l} != {r}"
        return l
    result.get = get
    def set(new, *args, **kwargs):
        l = left.set(new, *args, **kwargs)
        r = right.set(new, *args, **kwargs)
        return l,r
    result.set = set
    return result
BoundLens.__eq__ = merge_optics_with_equal_foci

def boundlens(get : Callable[[],A], set : Callable[[B],T]) -> BoundLens[None,T,A,B]:
    return BoundLens(None, o.Lens(lambda none: get(), lambda none, new: set(new)))

def regex(s : str, *args, **kwargs) -> UnboundLens[str, str, str, str]:
    r = re.compile(s)
    UnboundLens(o.Lens(lambda string: r.search(string, *args, **kwargs).group(), lambda old, new: r.sub(new, old, *args, **kwargs)))
filetostring = lambda filename: boundlens(lambda: open(filename).read(), lambda new: open(filename, "w").write(new))
stringtojson = UnboundLens(o.Isomorphism(json.loads, json.dumps))
yxtorc       = UnboundLens(o.Isomorphism(lambda yx: (yx[0], yx[1]//10), lambda yx: (yx[0], yx[1]*10)))
dictstolists = UnboundLens(o.Isomorphism(lambda dicts: [list(dicts[0].keys())] + [list(row.values()) for row in dicts], lambda lists: [dict(zip(lists[0], row)) for row in lists][1:]))

class CodeSheet(List[dict]):
    def __init__(self, dicts):
        name = varname.nameof(self)
        self.dicts = dicts
        filetojson = filetostring(__file__) & regex(name + r"= CodeSheet\((.*)\)", re.DOTALL) & stringtojson
        runtimetodict = boundlens(lambda: self, lambda new: setattr(sys.modules[__name__], name, new))
        self.sheet = filetojson == runtimetodict

#typesheet = CodeSheet([...])

def main(stdscr : curses.window):
    rc = boundlens(lambda: stdscr.getyx(),lambda yx: stdscr.move(*yx)) & yxtorc
    filename = sys.argv[1]
    sheets = [filetostring(filename) & stringtojson & dictstolists]
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
            {"key": "KEY_UP"   , "desc": "go up"      , "do": lambda: rc[0]-1     , "undo": lambda: rc[0]+1},
            {"key": "KEY_DOWN" , "desc": "go down"    , "do": lambda: rc[0]+1     , "undo": lambda: rc[0]-1},
            {"key": "KEY_RIGHT", "desc": "go right"   , "do": lambda: rc[1]+1     , "undo": lambda: rc[1]-1},
            {"key": "KEY_LEFT" , "desc": "go left"    , "do": lambda: rc[1]-1     , "undo": lambda: rc[1]+1},
            {"key": "d"        , "desc": "flush cell" , "do": lambda: cell.set(""), "undo": lambda: cell.set(value)},
            {"key": "e"        , "desc": "edit cell"  , "do": lambda: cell.set(stdscr.getstr().decode("utf-8")), "undo": lambda: cell.set(value)},
            {"key": "q"        , "desc": "quit"       , "do": lambda: sys.exit(0), "undo": None},
            {"key": "h"        , "desc": "help"       , "do": lambda: openkeymap(), "undo": lambda: closekeymap()},
            {"key": "c"        , "desc": "commands"   , "do": lambda: opencommands(), "undo": None},
        ]
        key = stdscr.getkey()
        for cmd in help:
            if cmd["key"] == key:
                cmd["do"]()
                commandlog.append(cmd)
                break

if __name__ == "__main__":
    curses.wrapper(main)