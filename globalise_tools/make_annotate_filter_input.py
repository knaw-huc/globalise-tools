#!/usr/bin/env python3
import argparse
import csv
from argparse import Namespace

import orjson
from icecream import ic
from loguru import logger


def get_arguments() -> Namespace:
    parser = argparse.ArgumentParser(
        description="Extract ner offsets from a given entity annotation page, and export them as csv",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("entity_annotation_page",
                        help="The json file containing the entity annotation page",
                        type=str,
                        nargs='+'
                        )
    return parser.parse_args()


@logger.catch
def main():
    args = get_arguments()
    annotation_page_paths = args.entity_annotation_page
    headers = ["page", "tag", "start", "end", "label"]
    rows = []
    annotations_parsed = 0
    for path in annotation_page_paths:
        page_id = path.split("/")[-1].replace(".json", "")
        print(f"<= {path}")
        with open(path, 'rb') as f:
            page = orjson.loads(f.read())
        items = page["items"]
        for annotation in items:
            bodies = annotation["body"]
            classificatory_bodies = [b for b in bodies if b["type"] == "ClassificatoryStatus"]
            if classificatory_bodies:
                first_body = classificatory_bodies[0]
                tag = first_body["has_classificatory_subject"]["type"]
                label = first_body["label"]
                selector = annotation["target"][0]["selector"][1]
                start = selector["start"]
                end = selector["end"]
                rows.append([page_id, tag, start, end, label])

            appellative_bodies = [b for b in bodies if b["type"] == "AppellativeStatus"]
            if appellative_bodies:
                first_body = appellative_bodies[0]
                tag = first_body["has_appellative_subject"]["type"]
                label = first_body["label"]
                selector = annotation["target"][0]["selector"][1]
                start = selector["start"]
                end = selector["end"]
                rows.append([page_id, tag, start, end, label])

            dimension_bodies = [b for b in bodies if b["type"] == "Dimension"]
            if dimension_bodies:
                tag = "Dimension"
                selectors = annotation["target"][0]["selector"]
                label = selectors[0]["exact"]
                start = selectors[1]["start"]
                end = selectors[1]["end"]
                rows.append([page_id, tag, start, end, label])

            if not classificatory_bodies and not appellative_bodies and not dimension_bodies:
                ic(annotation)
            annotations_parsed += 1

    out_path = f"work/entity-tags.tsv"
    print(f"=> {out_path}")
    with open(out_path, mode='w', newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        writer.writerow(headers)
        writer.writerows(rows)

    logger.info(f"annotations parsed: {annotations_parsed}")
    logger.info(f"rows extracted: {len(rows)}")


if __name__ == '__main__':
    main()
