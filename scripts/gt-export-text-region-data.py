#!/usr/bin/env python3
import glob
import json
import os

import pagexml.parser as px
from loguru import logger

import globalise_tools.tools as gt


def read_inventories_of_interest() -> list[str]:
    path = "data/inventories-of-interest.json"
    logger.info(f"<= {path}")
    with open(path) as f:
        inventories = json.load(f)
    return inventories


def export_page(pagexml_path: str):
    logger.info(f"<= {pagexml_path}")
    scan_doc = px.parse_pagexml_file(pagexml_path)
    regions = []

    for tr in scan_doc.get_text_regions_in_reading_order():
        text_words_pair = gt.joined_lines(tr)
        text = text_words_pair.text
        main_type = tr.type[-1]
        if text and main_type != "pagexml_doc":
            region = {
                "type": main_type,
                "text": text.strip()
            }
            regions.append(region)

    base = "/".join(pagexml_path.split("/")[-2:]).replace(".xml", "")
    output_path = f"out/ioi/{base}.json"
    logger.info(f"=> {output_path}")
    with open(output_path, "w") as f:
        json.dump(regions, fp=f, indent=4, ensure_ascii=False)


def pagexml_paths(inv_nr) -> list[str]:
    return sorted(glob.glob(f"/Users/bram/c/data/globalise/pagexml/{inv_nr}/NL-HaNA_1.04.02_{inv_nr}_*.xml"))


def export(inventory_number: str):
    output_path = f"out/ioi/{inventory_number}"
    os.makedirs(output_path, exist_ok=True)
    for pagexml_path in pagexml_paths(inventory_number):
        export_page(pagexml_path)


@logger.catch
def main():
    for inventory_number in read_inventories_of_interest():
        export(inventory_number)


if __name__ == '__main__':
    main()
