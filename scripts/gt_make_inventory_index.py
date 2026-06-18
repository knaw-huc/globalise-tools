#!/usr/bin/env python3
import argparse
import os
from argparse import Namespace
from typing import NamedTuple, Any

from icecream import ic
from jsonpath_ng import parse
from loguru import logger

import globalise_tools.io_tools as rw


# globalise issue:
# https://github.com/globalise-huygens/glob-portal-infomodel/issues/58

def get_arguments() -> Namespace:
    parser = argparse.ArgumentParser(
        description="Extract ner offsets from entity annotation page of the given inventory number, and export them as json, as well as the normalized text of the given inventory number",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-p", "--placename-alternatives-file",
                        help="The json file containing the placename alternatives",
                        type=str,
                        )
    parser.add_argument("inventory_number",
                        help="The inventory number to process",
                        type=str,
                        nargs='+'
                        )
    return parser.parse_args()


class NerRecord(NamedTuple):
    page_id: str
    tag: str
    identifier: str = None
    pref_label: str = None
    match_label: str = None
    text: str = ""
    start_in_page: int = 0
    end_in_page: int = 0
    start_in_doc: int = 0
    end_in_doc: int = 0


items_expr = parse("items")
body_expr = parse("body")


class DocumentProcessor:

    def __init__(self, inventory_number: str, document: dict[str, Any], preferred_placenames):
        self.place_annotation_count = 0
        self.places_identified = 0
        self.document_id = inventory_number
        self.document = document
        self.document_text = ""
        self.entity_records = []
        self.annotations_parsed = 0
        self.preferred_placenames = preferred_placenames

    def process(self):
        print(f"# document id  : {self.document_id}")

        for page_id in self.document["page_ids"]:
            self._process_page(page_id)

        self._enrich_place_annotations()
        print(f"- annotations parsed          : {self.annotations_parsed}")
        print(f"- records extracted           : {len(self.entity_records)}")
        print(f"- place annotations extracted : {self.place_annotation_count}")
        print(f"- places identified           : {self.places_identified}")
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
                NerRecord(page_id=page_id, tag=tag, start_in_page=start, end_in_page=end,
                          start_in_doc=start + page_offset, end_in_doc=end + page_offset, text=label)
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
                    text=label
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
                    text=label
                )
            )

        if not classificatory_bodies and not appellative_bodies and not dimension_bodies:
            logger.warning(f"No suitable body found in annotation")
            ic(annotation)

    def _export(self):
        annotations = [r._asdict() for r in self.entity_records]
        data = self.document.copy()
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

    def _enrich_place_annotations(self):
        self.entity_records = [self._enrich_place_annotation(a) for a in self.entity_records]

    def _enrich_place_annotation(self, record: NerRecord) -> NerRecord:
        if record.tag == "Place":
            self.place_annotation_count += 1
            key = record.text.lower()
            if key in self.preferred_placenames:
                first_preference = self.preferred_placenames[key][0]
                new_record = NerRecord(
                    page_id=record.page_id,
                    tag=record.tag,
                    start_in_page=record.start_in_page,
                    end_in_page=record.end_in_page,
                    start_in_doc=record.start_in_doc,
                    end_in_doc=record.end_in_doc,
                    text=record.text,
                    identifier=first_preference["identifier"],
                    pref_label=first_preference["prefLabel"],
                    match_label=first_preference["matchedLabel"],
                )
                self.places_identified += 1
                return new_record
        return record


@logger.catch
def main():
    args = get_arguments()

    if args.placename_alternatives_file is not None:
        preferred_placenames = rw.read_json(args.placename_alternatives_file)
    else:
        preferred_placenames = {}
    inventory_numbers = args.inventory_number

    globalise_documents_path = "data/globalise-documents.json"
    document_idx = _load_document_idx(globalise_documents_path)

    for inventory_number in inventory_numbers:
        if inventory_number in document_idx:
            document = document_idx[inventory_number]
            DocumentProcessor(inventory_number, document, preferred_placenames).process()
        else:
            logger.warning(f"invalid inventory number: {inventory_number} (not found in {globalise_documents_path})")


def _load_document_idx(globalise_documents_path: str) -> dict[Any, Any]:
    document_data = rw.read_json(globalise_documents_path)
    document_idx = {r["inventory_number"]: r for r in document_data}
    return document_idx


if __name__ == '__main__':
    main()
