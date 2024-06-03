#!/usr/bin/env python3
import csv
import glob
import os

import pagexml.parser as px
from loguru import logger

base_pagexml_path = "/Users/bram/workspaces/globalise/pagexml"


@logger.catch
def main():
    inv_nrs = sorted(
        [p.split("/")[-1] for p in glob.glob(f"{base_pagexml_path}/*") if os.path.isdir(p)])
    for i in inv_nrs:
        process_inv(i)


def pagexml_paths(inv_nr: str) -> list[str]:
    return sorted(glob.glob(f"{base_pagexml_path}/{inv_nr}/NL-HaNA_1.04.02_{inv_nr}_*.xml"))


def process_inv(inv_nr: str):
    file_name = f"/Users/bram/workspaces/globalise/{inv_nr}-lines.tsv"
    print(f"=> {file_name}")
    with open(file_name, mode='w', newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        writer.writerow(["inv_nr", "page_no", "line_id", "line_text"])
        for path in pagexml_paths(inv_nr):
            parts = path.split('/')
            page_no = parts[-1].split('_')[-1].replace('.xml', '')
            scan_doc = px.parse_pagexml_file(pagexml_file=path)
            for tr in scan_doc.get_text_regions_in_reading_order():
                if tr.lines:
                    for l in tr.lines:
                        if l.text:
                            writer.writerow([inv_nr, page_no, l.id, l.text])


if __name__ == '__main__':
    main()
