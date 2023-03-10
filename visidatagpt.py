# This shall become a reimplementation of VisiData, the terminal spreadsheet.
# It'll use minimum lines of code and add natural-language processing.
# This version merely lets the user navigate a csv file.

import curses
import csv
import sys

def main(stdscr : curses.window):
    with open(sys.argv[1]) as f:
        reader = csv.reader(f)
        data = list(reader)
        for y, row in enumerate(data):
            for x, cell in enumerate(row):
                stdscr.addstr(y, 10*x, cell)
    row, col = 0, 0
    stdscr.move(row, col)
    while True:
        key = stdscr.getkey()
        if key == "q": break
        elif key == "KEY_UP": row -= 1
        elif key == "KEY_DOWN": row += 1
        elif key == "KEY_RIGHT": col += 10
        elif key == "KEY_LEFT": col -= 10
        stdscr.move(row, col)

if __name__ == "__main__":
    curses.wrapper(main)