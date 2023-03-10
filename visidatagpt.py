# This shall become a reimplementation of VisiData, the terminal spreadsheet.
# It'll use minimum lines of code and add natural-language processing.
# This initial commit merely displays a csv file.

import sys
import csv

if __name__ == '__main__':
    with open(sys.argv[1]) as f:
        reader = csv.reader(f)
        for row in reader:
            print(row)