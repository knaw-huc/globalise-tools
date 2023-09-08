#!/usr/bin/env python3
import json

from collections import defaultdict

with open('data/pagexml-2023-05-30-contents.txt') as f:
    lines = f.readlines()
pagexml_map = defaultdict(list)
pagexml_ids = set()
for line in lines:
    parts = line.strip().split('/')
    pagexml_id = parts[-1].replace('.xml', '')
    pagexml_ids.add(pagexml_id)
for pagexml_id in sorted(list(pagexml_ids)):
    inv_nr = pagexml_id.split('_')[-2]
    pagexml_map[inv_nr].append(pagexml_id)
with open('data/pagexml_map.json', 'w') as f:
    json.dump(pagexml_map, f)
