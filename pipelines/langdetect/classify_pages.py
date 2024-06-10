#!/usr/bin/env python3

import sys
from collections import Counter

COL_INV = 0
COL_PAGE = 1
COL_LANG = 3

print("inv_nr\tpage_no\tlang\tscore")
for filename in sys.argv[1:]:
    prev_inv = None
    prev_page = None
    langs = Counter() 
    with open(filename,'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i == 0:
                #skip header
                continue
            fields = line.strip().split("\t")
            if fields[COL_INV] != prev_inv or fields[COL_PAGE] != prev_page:
                if prev_inv and prev_page:
                    for lang, count in langs.most_common(1):
                        if count > 3: #a page must have more than three lines to be considered
                            score = count / langs.total()
                            print(f"{prev_inv}\t{prev_page}\t{lang}\t{score}")
                prev_inv = fields[COL_INV]
                prev_page = fields[COL_PAGE]
                langs.clear()
            elif fields[COL_LANG] != "unknown":
                langs[fields[COL_LANG]] += 1
        #wrap up after last one: 
        if prev_inv and prev_page and len(langs) > 0:
            for lang, count in langs.most_common(1):
                if count > 3: #a page must have more than three lines to be considered
                    score = count / langs.total()
                    print(f"{prev_inv}\t{prev_page}\t{lang}\t{score}")
