# terminal spreadsheet with natural language processing

import curses
import csv
import sys

def main(stdscr : curses.window):
    with open(sys.argv[1]) as f:
        reader = csv.reader(f)
        for y, row in enumerate(list(reader)):
            for x, cell in enumerate(row):
                stdscr.addstr(y, 10*x, cell)
    stdscr.move(0, 0)
    commandlog = []
    while True:
        row, col = stdscr.getyx()
        data = stdscr.instr(row, col, 10)
        move = lambda r,c: {"do": lambda: stdscr.move(row+r, col+c), "undo": lambda: stdscr.move(row, col)}
        keymap ={"d": {"do": lambda: stdscr.addstr(row, col, " "*10), "undo": lambda: stdscr.addstr(row, col, data)}
                ,"KEY_UP"  : move(-1, 0)
                ,"KEY_DOWN": move(1, 0)
                ,"KEY_RIGHT": move(0, 10)
                ,"KEY_LEFT": move(0, -10)
                ,"q": {"do": lambda: sys.exit(0), "undo": lambda: print("Can't undo that.")}
                }
        cmd = keymap[stdscr.getkey()]
        commandlog.append(cmd)
        cmd["do"]()

if __name__ == "__main__":
    curses.wrapper(main)