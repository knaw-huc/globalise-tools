#!/usr/bin/env python3
import argparse
import os
from argparse import Namespace
from typing import NamedTuple, Any

from icecream import ic
from jsonpath_ng import parse
from loguru import logger

import globalise_tools.io_tools as rw


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
    inventory_numbers = args.inventory_number

    document_data = rw.read_json("data/globalise-documents.json")
    document_idx = {r["inventory_number"]: r for r in document_data}

    for inventory_number in inventory_numbers:
        document = document_idx[inventory_number]
        process_document(inventory_number, document)


def process_document(inventory_number, document):
    print(f"# inventory number  : {inventory_number}")

    inventory_text = ""
    records = []
    annotations_parsed = 0
    for page_id in document["page_ids"]:
        annotations_parsed, inventory_text = process_page(page_id, inventory_number, records, annotations_parsed,
                                                          inventory_text)

    print(f"- annotations parsed: {annotations_parsed}")
    print(f"- records extracted : {len(records)}")
    print("")

    export(inventory_number, inventory_text, records)


def process_page(
        page_id: str,
        inventory_number: str,
        records: list[Any],
        annotations_parsed: int,
        inventory_text: str
) -> tuple[int, str]:
    transcription_page_path = f"work/{inventory_number}/transcriptions/{page_id}.json"
    transcription_page = rw.read_json(transcription_page_path, quiet=True)
    items = transcription_page["items"]
    normalized_page_annotation = [i for i in items if i["id"].endswith("#page-normalized")][0]
    if "body" in normalized_page_annotation:
        page_text = normalized_page_annotation["body"][0]["value"]
        page_offset = len(inventory_text)
        inventory_text += page_text

        possible_entities_page_path = f"work/{inventory_number}/entities/{page_id}.json"
        if os.path.exists(possible_entities_page_path):
            entities_page_path = possible_entities_page_path
            page = rw.read_json(entities_page_path, quiet=True)
            items = page["items"]
            for annotation in items:
                annotations_parsed = process_annotation(annotation, annotations_parsed, page_id, page_offset, records)
    return annotations_parsed, inventory_text


def process_annotation(annotation: dict[str, Any], annotations_parsed: int, page_id, page_offset: int,
                       records: list[Any]) -> int:
    bodies = annotation["body"]
    classificatory_bodies = [b for b in bodies if b["type"] == "ClassificatoryStatus"]
    for body in classificatory_bodies:
        tag = body["has_classificatory_subject"]["type"]
        label = body["label"]
        selector = annotation["target"][0]["selector"][1]
        start = selector["start"]
        end = selector["end"]
        records.append(NerRecord(page_id=page_id, tag=tag, start_in_page=start, end_in_page=end,
                                 start_in_doc=start + page_offset, end_in_doc=end + page_offset,
                                 label=label))

    appellative_bodies = [b for b in bodies if b["type"] == "AppellativeStatus"]
    for body in appellative_bodies:
        tag = body["has_appellative_subject"]["type"]
        label = body["label"]
        selector = annotation["target"][0]["selector"][1]
        start = selector["start"]
        end = selector["end"]
        records.append(NerRecord(page_id=page_id, tag=tag, start_in_page=start, end_in_page=end,
                                 start_in_doc=start + page_offset, end_in_doc=end + page_offset,
                                 label=label))

    dimension_bodies = [b for b in bodies if b["type"] == "Dimension"]
    if dimension_bodies:
        tag = "Dimension"
        selectors = annotation["target"][0]["selector"]
        label = selectors[0]["exact"]
        start = selectors[1]["start"]
        end = selectors[1]["end"]
        records.append(NerRecord(page_id=page_id, tag=tag, start_in_page=start, end_in_page=end,
                                 start_in_doc=start + page_offset, end_in_doc=end + page_offset,
                                 label=label))

    if not classificatory_bodies and not appellative_bodies and not dimension_bodies:
        ic(annotation)
    annotations_parsed += 1
    return annotations_parsed


def export(inventory_number, inventory_text: str, records: list[Any]):
    rw.write_tsv(
        path=f"work/{inventory_number}/entity-tags.tsv",
        headers=list(records[0]._asdict().keys()),
        records=[r._asdict().values() for r in records]
    )

    rw.write_json(
        path=f"work/{inventory_number}/entity-tags.json",
        data=[r._asdict() for r in records]
    )

    rw.write_text(
        path=f"work/{inventory_number}/document.txt",
        text=inventory_text
    )


if __name__ == '__main__':
    main()
