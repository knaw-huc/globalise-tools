#!/usr/bin/env python3
import argparse
import os
from argparse import Namespace
from typing import NamedTuple, Any

from Levenshtein import distance
from icecream import ic
from jsonpath_ng import parse
from loguru import logger

import globalise_tools.io_tools as rw
import globalise_tools.url_factory as uf
from globalise_tools.url_factory import AnnotationPageType


# globalise issue:
# https://github.com/globalise-huygens/glob-portal-infomodel/issues/58

def get_arguments() -> Namespace:
    parser = argparse.ArgumentParser(
        description="Extract ner offsets from entity annotation page of the given inventory number, and export them as json, as well as the normalized text of the given inventory number",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-d", "--document-definitions-file",
                        help="The csv file containing the document definitions",
                        type=str,
                        required=True,
                        )
    parser.add_argument("-p", "--placename-alternatives-file",
                        help="The json file containing the placename alternatives",
                        type=str,
                        required=True,
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

    def __init__(self, inventory_number: str, document_id: str, document: dict[str, Any], preferred_placenames):
        self.inventory_number = inventory_number
        self.document_id = document_id
        self.document = document
        self.document_text = ""
        self.preferred_placenames = preferred_placenames
        self.place_annotation_count = 0
        self.places_identified = 0
        self.entity_records = []
        self.annotations_parsed = 0

    def process(self):
        first_page = int(self.document["startScan"].split("_")[-1])
        last_page = int(self.document["endScan"].split("_")[-1])
        page_ids = [f"NL-HaNA_1.04.02_{self.inventory_number}_{i:04d}" for i in range(first_page, last_page + 1)]
        for page_id in page_ids:
            self._process_page(page_id)
        self._enrich_place_annotations()
        return {
            "id": self.document["id"],
            "name": self.document["name"],
            "title": self.document["title"],
            "settlement": self.document["settlement"],
            "normalized_text": {
                "value": self.document_text,
                "DataPositionSelector": {
                    "source": "",
                    "start": 0,
                    "end": 0
                }
            },
            "method": self.document["method"],
            "start_page": self.document["startScan"],
            "end_page": self.document["endScan"],
            "start_date": self.document["dateStart"],
            "end_date": self.document["dateEnd"],
            "number_of_pages": self.document["numberOfScans"],
            "annotations": [r._asdict() for r in self.entity_records],
        }

    def _process_page(self, page_id: str) -> None:
        transcription_page = self._read_transcription_page(page_id)

        items = transcription_page["items"]
        normalized_page_annotation = [i for i in items if i["id"].endswith("#page-normalized")][0]
        if "body" in normalized_page_annotation:
            page_text = normalized_page_annotation["body"][0]["value"]
            page_offset = len(self.document_text)
            self.document_text += page_text

            entities_page = self._read_entities_page(page_id)
            if entities_page is not None:
                items = entities_page["items"]
                for annotation in items:
                    self._process_annotation(annotation, page_id, page_offset)
                    self.annotations_parsed += 1
        # else:
        #     logger.warning(f"expected body in annotation {normalized_page_annotation}")

    def _read_transcription_page(self, page_id: str) -> Any:
        transcription_page_path = f"work/{self.inventory_number}/transcriptions/{page_id}.json"
        if os.path.exists(transcription_page_path):
            transcription_page = rw.read_json(transcription_page_path, quiet=True)
        else:
            transcription_page_url = uf.annotation_page_url(AnnotationPageType.TRANSCRIPTIONS, page_id)
            transcription_page = rw.get_json(transcription_page_url, quiet=True)
        return transcription_page

    def _read_entities_page(self, page_id: str) -> Any:
        entities_page_path = f"work/{self.inventory_number}/entities/{page_id}.json"
        if os.path.exists(entities_page_path):
            entities_page = rw.read_json(entities_page_path, quiet=True)
        else:
            entities_page_url = uf.annotation_page_url(AnnotationPageType.ENTITIES, page_id)
            entities_page = rw.get_json(entities_page_url, quiet=True)
        return entities_page

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

    def _enrich_place_annotations(self):
        self.entity_records = [self._enrich_place_annotation(a) for a in self.entity_records]

    def _enrich_place_annotation(self, record: NerRecord) -> NerRecord:
        if record.tag == "Place":
            self.place_annotation_count += 1
            key = self._matching_preferred_placename(record)
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

    def _matching_preferred_placename(self, record: NerRecord) -> str | None:
        key = record.text.lower()
        if key in self.preferred_placenames:
            return key

        original_length = len(key)
        best_match = None
        best_distance = 5
        for k in self.preferred_placenames:
            other_length = len(k)
            d = distance(key, k, score_cutoff=best_distance - 1)
            if d < best_distance and d < min(original_length, other_length):
                best_match = k
                best_distance = d

        return best_match


class InventoryProcessor:

    def __init__(self, inventory_number: str, inventory: dict[str, Any], document_definitions, preferred_placenames):
        self.inventory_number = inventory_number
        self.inventory = inventory
        self.document_definitions = document_definitions
        self.preferred_placenames = preferred_placenames
        self.records_extracted = 0
        self.place_annotation_count = 0
        self.places_identified = 0
        self.inventory_text = ""
        self.annotations_parsed = 0
        self.documents = []

    def process(self):
        print(f"# inventory number  : {self.inventory_number}")

        total_documents = len(self.document_definitions)
        for i, document in enumerate(self.document_definitions):
            # ic(document)
            doc_id = document['name']
            print(f"## {i + 1}/{total_documents} : {doc_id}")
            dp = DocumentProcessor(self.inventory_number, doc_id, document, self.preferred_placenames)
            doc = dp.process()
            self.documents.append(doc)
            self.annotations_parsed += dp.annotations_parsed
            self.places_identified += dp.places_identified
            self.place_annotation_count += dp.place_annotation_count
            self.records_extracted += len(dp.entity_records)

        print(f"- documents processed         : {len(self.documents)}")
        print(f"- annotations parsed          : {self.annotations_parsed}")
        print(f"- records extracted           : {self.records_extracted}")
        print(f"- place annotations extracted : {self.place_annotation_count}")
        print(f"- places identified           : {self.places_identified}")
        print("")
        self._export()

    def _export(self):
        data = self.inventory.copy()
        default_start_date = self.inventory["date_start"]
        default_end_date = self.inventory["date_end"]
        data["documents"] = [self._add_default_dates(d, default_start_date, default_end_date) for d in self.documents]
        rw.write_json(
            path=f"work/{self.inventory_number}/index.json",
            data=data
        )

        # rw.write_text(
        #     path=f"work/{self.inventory_number}/document.txt",
        #     text=self.document_text
        # )

    @staticmethod
    def _add_default_dates(d: dict[str, Any], default_start_date: str, default_end_date: str) -> dict[str, Any]:
        if d["start_date"] == "":
            d["start_date"] = default_start_date
        if d["end_date"] == "":
            d["end_date"] = default_end_date
        return d


@logger.catch
def main():
    args = get_arguments()

    if args.placename_alternatives_file is not None:
        preferred_placenames = rw.read_json(args.placename_alternatives_file)
    else:
        preferred_placenames = {}

    if args.document_definitions_file is not None:
        document_definitions_per_inventory = rw.read_json(args.document_definitions_file)
    else:
        document_definitions_per_inventory = {}

    inventory_numbers = args.inventory_number

    globalise_inventories_path = "data/globalise-inventories.json"  # TODO: move to args
    inventory_idx = _load_inventory_idx(globalise_inventories_path)

    for inventory_number in inventory_numbers:
        if inventory_number in inventory_idx:
            inventory = inventory_idx[inventory_number]
            document_definitions = document_definitions_per_inventory[inventory_number]
            InventoryProcessor(inventory_number, inventory, document_definitions, preferred_placenames).process()
        else:
            logger.warning(f"invalid inventory number: {inventory_number} (not found in {globalise_inventories_path})")


def _load_inventory_idx(globalise_documents_path: str) -> dict[Any, Any]:
    document_data = rw.read_json(globalise_documents_path)
    document_idx = {r["inventory_number"]: r for r in document_data}
    return document_idx


if __name__ == '__main__':
    main()
