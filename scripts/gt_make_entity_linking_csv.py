#!/usr/bin/env python3
import argparse
import os
from argparse import Namespace
from typing import Any, NamedTuple

from loguru import logger

import globalise_tools.io_tools as rw


# headers = ["annotation_id","status_id","annotation_entity_type","entity_id","offset_inventory","offset_scan,prefix","exact","suffix",classified_as,entity_uri,entity_type,entity_label,concept_uri,concept_label,begin_of_the_begin,end_of_the_end]
# See https://github.com/globalise-huygens/glob-portal-infomodel/issues/59

class Record(NamedTuple):
    annotation_id: str = ""
    status_id: str = ""
    annotation_entity_type: str = ""
    entity_id: str = ""
    offset_inventory: str = ""
    offset_scan: str = ""
    prefix: str = ""
    exact: str = ""
    suffix: str = ""
    classified_as: str = ""
    entity_uri: str = ""
    entity_type: str = ""
    entity_label: str = ""
    concept_uri: str = ""
    concept_label: str = ""
    begin_of_the_begin: str = ""
    end_of_the_end: str = ""


class EntityLinkFactory:

    def __init__(self, inventory_number: str, document: dict[str, Any]):
        self.inventory_number = inventory_number
        self.document = document
        self.records = []
        self.annotations_parsed = 0

    def make_entity_link_csv(self) -> None:
        path = f"work/{self.inventory_number}/entity_linking.csv"
        for page_id in self.document["page_ids"]:
            self._process_page(page_id)
        rw.write_csv(
            path=path,
            headers=self._headers(),
            records=self.records
        )

    def _headers(self) -> list[str]:
        return list(self.records[0]._asdict().keys())

    def _process_page(self, page_id: str):
        possible_entities_page_path = f"work/{self.inventory_number}/entities/{page_id}.json"
        if os.path.exists(possible_entities_page_path):
            entities_page_path = possible_entities_page_path
            page = rw.read_json(entities_page_path, quiet=True)
            items = page["items"]
            for annotation in items:
                self._process_annotation(annotation)
                self.annotations_parsed += 1

    def _process_annotation(self, annotation: dict[str, Any]):
        annotation_id = annotation["id"]
        bodies = annotation["body"]
        first_target = annotation["target"][0]
        first_target_selectors = first_target["selector"]

        classificatory_bodies = [b for b in bodies if b["type"] == "ClassificatoryStatus"]
        for body in classificatory_bodies:
            record = self._record_from_classificatory_body(body, annotation_id, first_target_selectors)
            self.records.append(record)

        appellative_bodies = [b for b in bodies if b["type"] == "AppellativeStatus"]
        for body in appellative_bodies:
            record = self._record_from_appellative_body(body, annotation_id, first_target_selectors)
            self.records.append(record)

    @staticmethod
    def _record_from_classificatory_body(
            body: dict[str, Any],
            annotation_id: str,
            selectors: list[dict[str, Any]]
    ) -> Record:
        text_quote_selector = selectors[0]
        text_position_selector = selectors[1]
        start = text_position_selector["start"]
        if "prefix" in text_quote_selector:
            prefix = text_quote_selector["prefix"]
        else:
            prefix = ""
        if "suffix" in text_quote_selector:
            suffix = text_quote_selector["suffix"]
        else:
            suffix = ""
        classificatory_subject = body["has_classificatory_subject"]
        return Record(
            annotation_id=annotation_id,
            status_id=body["id"],
            annotation_entity_type=classificatory_subject["type"],
            entity_id=classificatory_subject["id"],
            offset_inventory=start,
            offset_scan=start,
            prefix=prefix,
            exact=text_quote_selector["exact"],
            suffix=suffix,
            classified_as=body["classified_as"]["_label"]
        )

    @staticmethod
    def _record_from_appellative_body(
            body: dict[str, Any],
            annotation_id: str,
            selectors: list[dict[str, Any]]
    ) -> Record:
        text_quote_selector = selectors[0]
        text_position_selector = selectors[1]
        start = text_position_selector["start"]
        if "prefix" in text_quote_selector:
            prefix = text_quote_selector["prefix"]
        else:
            prefix = ""
        if "suffix" in text_quote_selector:
            suffix = text_quote_selector["suffix"]
        else:
            suffix = ""
        appellative_subject = body["has_appellative_subject"]
        return Record(
            annotation_id=annotation_id,
            status_id=body["id"],
            annotation_entity_type=appellative_subject["type"],
            entity_id=appellative_subject["id"],
            offset_inventory=start,
            offset_scan=start,
            prefix=prefix,
            exact=text_quote_selector["exact"],
            suffix=suffix,
            classified_as=body["classified_as"]["_label"]
        )


def get_arguments() -> Namespace:
    parser = argparse.ArgumentParser(
        description="Create an entity linking csv for the given inventory number",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("inventory_number",
                        help="The inventory number to process",
                        type=str,
                        nargs='+'
                        )
    return parser.parse_args()


@logger.catch
def main():
    args = get_arguments()
    inventory_numbers = args.inventory_number

    globalise_documents_path = "data/globalise-documents.json"
    document_idx = _load_document_idx(globalise_documents_path)

    for inventory_number in inventory_numbers:
        if inventory_number in document_idx:
            document = document_idx[inventory_number]
            EntityLinkFactory(inventory_number, document).make_entity_link_csv()
        else:
            logger.warning(f"invalid inventory number: {inventory_number} (not found in {globalise_documents_path})")


def _load_document_idx(globalise_documents_path: str) -> dict[Any, Any]:
    document_data = rw.read_json(globalise_documents_path)
    document_idx = {r["inventory_number"]: r for r in document_data}
    return document_idx


if __name__ == '__main__':
    main()
