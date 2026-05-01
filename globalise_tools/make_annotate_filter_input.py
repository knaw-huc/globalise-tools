#!/usr/bin/env python3
import argparse
import csv
from argparse import Namespace

import orjson
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

    out_path = f"work/entity-tags.tsv"
    print(f"=> {out_path}")
    with open(out_path, mode='w', newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        writer.writerow(headers)
        writer.writerows(rows)


if __name__ == '__main__':
    main()
