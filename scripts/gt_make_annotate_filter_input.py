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
        description="Extract ner offsets from entity annotation page of the given inventory number, and export them as json, as well as the normalized text of the given inventory number",
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


class DocumentProcessor:

    def __init__(self, inventory_number: str, document: dict[str, Any]):
        self.document_id = inventory_number
        self.document = document
        self.document_text = ""
        self.entity_records = []
        self.annotations_parsed = 0

    def process(self):
        print(f"# document id  : {self.document_id}")

        for page_id in self.document["page_ids"]:
            self._process_page(page_id)

        print(f"- annotations parsed: {self.annotations_parsed}")
        print(f"- records extracted : {len(self.entity_records)}")
        print("")

        self._export()

    def _process_page(self, page_id: str) -> None:
        transcription_page_path = f"work/{self.document_id}/transcriptions/{page_id}.json"
        transcription_page = rw.read_json(transcription_page_path, quiet=True)
        items = transcription_page["items"]
        normalized_page_annotation = [i for i in items if i["id"].endswith("#page-normalized")][0]
        if "body" in normalized_page_annotation:
            page_text = normalized_page_annotation["body"][0]["value"]
            page_offset = len(self.document_text)
            self.document_text += page_text

            possible_entities_page_path = f"work/{self.document_id}/entities/{page_id}.json"
            if os.path.exists(possible_entities_page_path):
                entities_page_path = possible_entities_page_path
                page = rw.read_json(entities_page_path, quiet=True)
                items = page["items"]
                for annotation in items:
                    self._process_annotation(annotation, page_id, page_offset)
                    self.annotations_parsed += 1

    def _process_annotation(self, annotation: dict[str, Any], page_id, page_offset: int):
        bodies = annotation["body"]
        classificatory_bodies = [b for b in bodies if b["type"] == "ClassificatoryStatus"]
        for body in classificatory_bodies:
            tag = body["has_classificatory_subject"]["type"]
            label = body["label"]
            selector = annotation["target"][0]["selector"][1]
            start = selector["start"]
            end = selector["end"]
            self.entity_records.append(
                NerRecord(
                    page_id=page_id,
                    tag=tag,
                    start_in_page=start,
                    end_in_page=end,
                    start_in_doc=start + page_offset,
                    end_in_doc=end + page_offset,
                    label=label
                )
            )

        appellative_bodies = [b for b in bodies if b["type"] == "AppellativeStatus"]
        for body in appellative_bodies:
            tag = body["has_appellative_subject"]["type"]
            label = body["label"]
            selector = annotation["target"][0]["selector"][1]
            start = selector["start"]
            end = selector["end"]
            self.entity_records.append(
                NerRecord(
                    page_id=page_id,
                    tag=tag,
                    start_in_page=start,
                    end_in_page=end,
                    start_in_doc=start + page_offset,
                    end_in_doc=end + page_offset,
                    label=label
                )
            )

        dimension_bodies = [b for b in bodies if b["type"] == "Dimension"]
        if dimension_bodies:
            tag = "Dimension"
            selectors = annotation["target"][0]["selector"]
            label = selectors[0]["exact"]
            start = selectors[1]["start"]
            end = selectors[1]["end"]
            self.entity_records.append(
                NerRecord(
                    page_id=page_id,
                    tag=tag,
                    start_in_page=start,
                    end_in_page=end,
                    start_in_doc=start + page_offset,
                    end_in_doc=end + page_offset,
                    label=label
                )
            )

        if not classificatory_bodies and not appellative_bodies and not dimension_bodies:
            logger.warning(f"No suitable body found in annotation")
            ic(annotation)

    def _export(self):
        # rw.write_tsv(
        #     path=f"work/{document_id}/entity-tags.tsv",
        #     headers=list(entity_records[0]._asdict().keys()),
        #     records=[r._asdict().values() for r in entity_records]
        # )

        annotations = [r._asdict() for r in self.entity_records]
        data= self.document.copy()
        data["annotations"] = annotations
        data.pop("page_ids")
        rw.write_json(
            path=f"work/{self.document_id}/index.json",
            data=data
        )

        rw.write_text(
            path=f"work/{self.document_id}/document.txt",
            text=self.document_text
        )


@logger.catch
def main():
    args = get_arguments()
    inventory_numbers = args.inventory_number

    globalise_documents_path = "data/globalise-documents.json"
    document_idx = _load_document_idx(globalise_documents_path)

    for inventory_number in inventory_numbers:
        if inventory_number in document_idx:
            document = document_idx[inventory_number]
            DocumentProcessor(inventory_number, document).process()
        else:
            logger.warning(f"invalid inventory number: {inventory_number} (not found in {globalise_documents_path})")


def _load_document_idx(globalise_documents_path: str) -> dict[Any, Any]:
    document_data = rw.read_json(globalise_documents_path)
    document_idx = {r["inventory_number"]: r for r in document_data}
    return document_idx


if __name__ == '__main__':
    main()
