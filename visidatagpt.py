import curses, sys, varname, json
from lenses import lens, bind

optics = bind(open("optics.json").read()).Json() #bootstrap
def plumb(source, target):
    for row in optics.get():
        s, t, what, forward, backward = row["s"], row["t"], row["what"], row["forward"], row["backward"]
        backwardargs = f"{t}" if what == "Iso" else f"{s},{t}"
        parens = f"(lambda {s}:{forward},lambda {backwardargs}:{backward})"
        optic = eval(f"lens.{what}{parens}")
        class Plumb(optic.__class__):
            def __repr__(self): return f"{what}{parens} from {s} to {t}"
            def __init__(self):
                self._optic = optic._optic
                self.s = s
                self.t = t
        poptic = Plumb()
        if source == s:
            if t == target: return poptic
            ott = plumb(t, target)
            if ott: return poptic & ott

def filesheet():
    return bind(f"{varname.varname()}.json") & plumb("file","dicts")
optics = filesheet()
cmds = filesheet()

@curses.wrapper
def main(window : curses.window):
    rc = bind(window) & plumb("window", "rc")
    commandlog = []
    sheets = [optics, cmds]
    while True:
        r,c = rc.get()
        sheet = sheets[-1]
        view = sheet & plumb("dicts","lists")
        colwidths = [max(len(str(cell)) for cell in col) for col in zip(*view.get())]
        window.clear()
        for rindex, row in enumerate(view.get()):
            for cindex, cell in enumerate(row):
                window.addstr(*(bind((rindex,cindex)) & plumb("yx","rc").flip()).get(), str(cell))
        rc.set((r,c))
        cell = view[r][c]
        value = cell.get()
        lastcmd = commandlog[-1] if commandlog else None
        key = window.getkey()
        for cmd in cmds.get():
            if cmd["key"] == key:
                exec(cmd["do"])
                commandlog.append(cmd)
                break