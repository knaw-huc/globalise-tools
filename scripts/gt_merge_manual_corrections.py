#!/usr/bin/env python3

"""For language detection: Merges manual corrections from a manually curated TSV file and automatic system output TSV file"""

import sys
import csv
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from collections import OrderedDict

def main():
    parser = ArgumentParser(
        description="Extract line text from pagexml files",
        formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('inputfile',
                        help="TSV file with language classifier or output per line (pages.lang.tsv)",
                        type=str)
    parser.add_argument('correctionsfile',
                        help="TSV file with manually corrected output",
                        type=str)
    args = parser.parse_args()

    data = OrderedDict()
    fieldnames = None
    for filename in (args.inputfile, args.correctionsfile):
        with open(filename, mode='r') as file:
            reader = csv.DictReader(file, delimiter="\t",quoting=csv.QUOTE_NONE)
            for row in reader:
                if fieldnames is None:
                    fieldnames = list(row.keys())
                key = (row['inv_nr'],row['page_no'])
                if filename == args.inputfile:
                    row['manual'] = 0
                else:
                    row['manual'] = 1
                data[key] = row
    assert fieldnames is not None
    if 'manual' not in fieldnames:
        fieldnames.append('manual')
    writer = csv.DictWriter(sys.stdout,fieldnames=fieldnames,delimiter="\t",quoting=csv.QUOTE_NONE,extrasaction='ignore')
    writer.writeheader()
    for key, row in data.items():
        writer.writerow(row)

if __name__ == '__main__':
    main()

