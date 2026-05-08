#!/usr/bin/env python3
import argparse
import csv
import json
from argparse import Namespace
from typing import NamedTuple

import orjson
from icecream import ic
from jsonpath_ng import parse
from loguru import logger


def get_arguments() -> Namespace:
    parser = argparse.ArgumentParser(
        description="Extract ner offsets from a given entity annotation page, and export them as csv and json",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("inventory_number",
                        help="The inventory number to process",
                        type=str,
                        nargs='+'
                        )
    return parser.parse_args()


class NerRecord(NamedTuple):
    page_id: str
    tag: str
    label: str
    start_in_page: int
    end_in_page: int
    start_in_doc: int
    end_in_doc: int


items_expr = parse("items")
body_expr = parse("body")


@logger.catch
def main():
    args = get_arguments()
    annotation_page_paths = args.entity_annotation_page
    records = []
    annotations_parsed = 0
    for path in annotation_page_paths:
        page_id = path.split("/")[-1].replace(".json", "")
        page_offset = 0
        print(f"<= {path}")
        with open(path, 'rb') as f:
            page = orjson.loads(f.read())
        items = page["items"]
        for annotation in items:
            bodies = annotation["body"]
            classificatory_bodies = [b for b in bodies if b["type"] == "ClassificatoryStatus"]
            for body in classificatory_bodies:
                tag = body["has_classificatory_subject"]["type"]
                label = body["label"]
                selector = annotation["target"][0]["selector"][1]
                start = selector["start"]
                end = selector["end"]
                records.append(NerRecord(page_id=page_id, tag=tag, start_in_page=start, end_in_page=end,
                                         start_in_doc=start + page_offset, end_in_doc=end + page_offset, label=label))

            appellative_bodies = [b for b in bodies if b["type"] == "AppellativeStatus"]
            for body in appellative_bodies:
                tag = body["has_appellative_subject"]["type"]
                label = body["label"]
                selector = annotation["target"][0]["selector"][1]
                start = selector["start"]
                end = selector["end"]
                records.append(NerRecord(page_id=page_id, tag=tag, start_in_page=start, end_in_page=end,
                                         start_in_doc=start + page_offset, end_in_doc=end + page_offset, label=label))

            dimension_bodies = [b for b in bodies if b["type"] == "Dimension"]
            if dimension_bodies:
                tag = "Dimension"
                selectors = annotation["target"][0]["selector"]
                label = selectors[0]["exact"]
                start = selectors[1]["start"]
                end = selectors[1]["end"]
                records.append(NerRecord(page_id=page_id, tag=tag, start_in_page=start, end_in_page=end,
                                         start_in_doc=start + page_offset, end_in_doc=end + page_offset, label=label))

            if not classificatory_bodies and not appellative_bodies and not dimension_bodies:
                ic(annotation)
            annotations_parsed += 1

    out_path = f"work/entity-tags.tsv"
    print(f"=> {out_path}")
    with open(out_path, mode='w', newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        headers = list(records[0]._asdict().keys())
        writer.writerow(headers)
        writer.writerows([r._asdict().values() for r in records])

    out_path = f"work/entity-tags.json"
    print(f"=> {out_path}")
    with open(out_path, mode='w', newline='') as file:
        json.dump([r._asdict() for r in records], file, indent=4)

    logger.info(f"annotations parsed: {annotations_parsed}")
    logger.info(f"records extracted: {len(records)}")


if __name__ == '__main__':
    main()
