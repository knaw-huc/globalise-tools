#!/usr/bin/env python3
import argparse
import itertools
import os
from argparse import Namespace
from dataclasses import dataclass
from typing import NamedTuple, Any, List

from Levenshtein import distance
from dataclasses_json import dataclass_json
from icecream import ic
from jsondataclass import from_dict
from jsonpath_ng import parse
from loguru import logger

import globalise_tools.io_tools as rw
import globalise_tools.url_factory as uf
from globalise_tools.url_factory import AnnotationPageType

# globalise issue:
# https://github.com/globalise-huygens/glob-portal-infomodel/issues/58

scheme2facet_name = {
    "Beroepen": "professions",
    "EAD": "ead",
    "GLOBALISE documenttypen": "documenttypes",
}


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
    annotation_id: str
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


@dataclass_json
@dataclass(frozen=True, eq=True)
class Element:
    identifier: str
    label: str


@dataclass_json
@dataclass(frozen=True, eq=True)
class Hierarchy:
    scheme: str
    elements: List[Element]

    def __hash__(self):
        return hash((self.scheme, tuple(self.elements)))


@dataclass_json
@dataclass(frozen=True, eq=True)
class Concept:
    uri: str
    label: str
    hierarchies: List[Hierarchy]

    def __hash__(self):
        return hash((self.uri, self.label, tuple(self.hierarchies)))


items_expr = parse("items")
body_expr = parse("body")


class DocumentProcessor:

    def __init__(self,
                 inventory_number: str,
                 document_id: str,
                 document: dict[str, Any],
                 preferred_placenames,
                 start_data_position: dict[str, int],
                 end_data_position: dict[str, int],
                 concepts_per_page: dict[str, dict[str, Any]],
                 annotation_enhancements: dict[str, dict[str, str]],
                 ead_identifier_lists: list[list[str]]
                 ) -> None:
        self.inventory_number = inventory_number
        self.document_id = document_id
        self.document = document
        self.document_text = ""
        self.concepts_per_page = concepts_per_page
        self.document_concepts = set()
        self.annotation_enhancements = annotation_enhancements
        self.preferred_placenames = preferred_placenames
        self.place_annotation_count = 0
        self.places_identified = 0
        self.profession_annotation_count = 0
        self.professions_identified = 0
        self.entity_records: list[NerRecord] = []
        self.annotations_parsed = 0
        self.start_data_position = start_data_position
        self.end_data_position = end_data_position
        self.ead_identifier_lists = ead_identifier_lists

    def process(self):
        first_page = int(self.document["start_scan"].split("_")[-1].replace("P", ""))
        last_page = int(self.document["end_scan"].split("_")[-1].replace("P", ""))
        if last_page < first_page:
            logger.error(f"Last page {last_page} is smaller than first page {first_page}")
            return None
        else:
            # TODO: handle divergent page numbering in 9817 and 10090
            page_ids = [f"NL-HaNA_1.04.02_{self.inventory_number}_{i:04d}" for i in range(first_page, last_page + 1)]
            for page_id in page_ids:
                self._process_page(page_id)
            self._enrich_place_and_profession_annotations()
            return self._make_doc(page_ids)

    def _make_doc(self, page_ids: list[str]) -> dict[str, Any] | None:
        if self.document_text == "":
            logger.warning("document text is empty, skipping")
            return None

        fields = [
            self._string_field("identifier", self.document["id"]),
            self._string_field("name", self.document["name"]),
            self._string_field("title", self.document["title"]),
            self._string_field("settlement", self.document["settlement"]),
            self._int_field("pages", self.document["number_of_scans"]),
            self._string_field("start_page", self.document["start_scan"]),
            self._string_field("end_page", self.document["end_scan"]),
            self._string_field("inventorynumber", self.inventory_number),
            self._annotatedtext_field(page_ids),
            self._daterange_field(self.document["date_start"], self.document["date_end"]),
            self._facet_field("ead", self.ead_identifier_lists)
        ]

        if "type_hierarchies" in self.document and self.document["type_hierarchies"]:
            type_hierarchies = list(itertools.chain.from_iterable(self.document["type_hierarchies"]))
            grouped = itertools.groupby(type_hierarchies, lambda h: h["scheme"])
            for scheme, hierarchies in grouped:
                if scheme in scheme2facet_name:
                    facet_name = scheme2facet_name[scheme]
                    identifier_lists = [self._identifiers(th) for th in hierarchies]
                    fields.append(self._facet_field(facet_name, identifier_lists))
        if self.document_concepts:
            document_concept_hierarchy_lists = [c.hierarchies for c in self.document_concepts]
            document_concept_hierarchies = list(itertools.chain.from_iterable(document_concept_hierarchy_lists))
            sorted_document_concept_hierarchies = sorted(document_concept_hierarchies, key=lambda h: h.scheme)
            grouped_document_concept_hierarchies = itertools.groupby(sorted_document_concept_hierarchies,
                                                                     key=lambda h: h.scheme)
            for scheme, in_hierarchies in grouped_document_concept_hierarchies:
                if scheme in scheme2facet_name:
                    facet_name = scheme2facet_name[scheme]
                    identifier_lists = [self._identifiers(th) for th in in_hierarchies]
                    fields.append(self._facet_field(facet_name, identifier_lists))

        return {
            "fields": fields
        }

    @staticmethod
    def _identifiers(hierarchy: dict[str, Any] | Hierarchy) -> list[str]:
        if isinstance(hierarchy, Hierarchy):
            return [e.identifier for e in hierarchy.elements]
        else:
            return [e["identifier"] for e in hierarchy["elements"]]

    @staticmethod
    def _facet_field(name: str, identifier_lists: list[list[str]]) -> dict[str, Any]:
        return dict(
            name=name,
            type="facet",
            value=identifier_lists
        )

    def _annotatedtext_field(self, page_ids: list[str]) -> dict[str, Any]:
        return dict(
            name="content",
            type="annotatedtext",
            store=True,
            value=self.document_text,
            DataPositionSelector=dict(
                source=f"https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/inventory:{self.inventory_number}.txt",
                start=self.start_data_position[page_ids[0]],
                end=self.end_data_position[page_ids[-1]]),
            annotations=self._simplified_annotations())

    @staticmethod
    def _daterange_field(start_date, end_date) -> dict[str, Any]:
        return dict(
            name="date",
            type="daterange",
            value={
                "from": start_date,
                "to": end_date
            }
        )

    @staticmethod
    def _string_field(name: str, value: str) -> dict[str, Any]:
        return dict(
            name=name,
            type="string",
            store=True,
            value=value
        )

    @staticmethod
    def _int_field(name: str, value: int) -> dict[str, Any]:
        return dict(
            name=name,
            type="integer",
            store=True,
            value=value
        )

    def _make_doc0(self, page_ids: list[str]) -> dict[str, Any]:
        doc = dict(
            id=self.document["id"],
            name=self.document["name"],
            title=self.document["title"],
            settlement=self.document["settlement"],
            normalized_text=dict(
                value=self.document_text,
                DataPositionSelector=dict(
                    source=f"https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/inventory:{self.inventory_number}.txt",
                    start=self.start_data_position[page_ids[0]],
                    end=self.end_data_position[page_ids[-1]])),
            method=self.document["method"],
            start_page=self.document["start_scan"],
            end_page=self.document["end_scan"],
            start_date=self.document["date_start"],
            end_date=self.document["date_end"],
            number_of_pages=self.document["number_of_scans"],
            annotations=[r._asdict() for r in self.entity_records]
        )
        if "hierarchies" not in doc:
            doc["hierarchies"] = []
        if "type_hierarchies" in self.document and self.document["type_hierarchies"]:
            doc["hierarchies"].append({
                "name": "DocumentType",
                "paths": self.document["type_hierarchies"],
            })
        if self.document_concepts:
            document_concept_hierarchy_lists = [c.hierarchies for c in self.document_concepts]
            document_concept_hierarchies = list(itertools.chain.from_iterable(document_concept_hierarchy_lists))
            sorted_document_concept_hierarchies = sorted(document_concept_hierarchies, key=lambda h: h.scheme)
            grouped_document_concept_hierarchies = itertools.groupby(sorted_document_concept_hierarchies,
                                                                     key=lambda h: h.scheme)
            concept_hierarchies = []
            for scheme, in_hierarchies in grouped_document_concept_hierarchies:
                paths = [[{"identifier": e.identifier, "title": e.label} for e in h.elements] for h in
                         in_hierarchies]
                concept_hierarchies.append({"name": scheme, "paths": paths})
            doc["hierarchies"].extend(concept_hierarchies)
        return doc

    def _process_page(self, page_id: str) -> None:
        transcription_page = self._read_transcription_page(page_id)
        if page_id in self.concepts_per_page:
            page_concepts = [from_dict(c, Concept) for c in self.concepts_per_page[page_id]]
            self.document_concepts.update(page_concepts)

        if transcription_page and "items" in transcription_page:
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
            logger.warning(f"Transcription page not found: {page_id}, reading from url")
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
        annotation_id = annotation["id"]
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
                    annotation_id=annotation_id,
                    page_id=page_id,
                    tag=tag,
                    start_in_page=start,
                    end_in_page=end,
                    start_in_doc=start + page_offset,
                    end_in_doc=end + page_offset,
                    text=label
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
                    annotation_id=annotation_id,
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
                    annotation_id=annotation_id,
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

    def _enrich_place_and_profession_annotations(self):
        self.entity_records = [self._enrich_place_annotation(a) for a in self.entity_records]
        self.entity_records = [self._enrich_profession_annotation(a) for a in self.entity_records]

    def _enrich_place_annotation(self, record: NerRecord) -> NerRecord:
        if record.tag == "Place":
            self.place_annotation_count += 1
            key = self._matching_preferred_placename(record)
            if key in self.preferred_placenames:
                first_preference = self.preferred_placenames[key][0]
                new_record = NerRecord(
                    annotation_id=record.annotation_id,
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

    def _enrich_profession_annotation(self, record: NerRecord) -> NerRecord:
        if record.tag == "Person":
            self.profession_annotation_count += 1
            if record.annotation_id in self.annotation_enhancements:
                new_record = NerRecord(
                    annotation_id=record.annotation_id,
                    page_id=record.page_id,
                    tag=record.tag,
                    start_in_page=record.start_in_page,
                    end_in_page=record.end_in_page,
                    start_in_doc=record.start_in_doc,
                    end_in_doc=record.end_in_doc,
                    text=record.text,
                    identifier=self.annotation_enhancements[record.annotation_id]["identifier"].split(":")[-1],
                )
                self.professions_identified += 1
                return new_record
        return record

    def _simplified_annotations(self) -> list[dict[str, Any]]:
        simplified_annotations = []
        for r in self.entity_records:
            simplified_annotations.append({
                "tag": r.tag,
                "from": r.start_in_doc,
                "to": r.end_in_doc,
                "text": r.text
            })
            if r.tag in ["Place", "Person"] and r.identifier is not None and r.identifier != "":
                simplified_annotations.append({
                    "tag": r.identifier,
                    "from": r.start_in_doc,
                    "to": r.end_in_doc,
                    "text": r.text
                })

        return simplified_annotations


class InventoryProcessor:

    def __init__(self, inventory_number: str, inventory: dict[str, Any], document_definitions, preferred_placenames):
        self.inventory_number = inventory_number
        self.inventory = inventory
        self.document_definitions = document_definitions
        self.preferred_placenames = preferred_placenames
        self.records_extracted = 0
        self.place_annotation_count = 0
        self.places_identified = 0
        self.profession_annotation_count = 0
        self.professions_identified = 0
        self.annotations_parsed = 0
        self.documents = []
        self.inventory_text, self.start_data_position, self.end_data_position = self._process_all_pages()
        self.concept_hierarchies_per_page = rw.read_json(f"work/{inventory_number}/entity_hierarchy.json")
        self.annotation_enhancements = rw.read_json(f"work/{inventory_number}/annotation_enhancements.json")

    def process(self):
        print(f"# inventory number  : {self.inventory_number}")

        total_documents = len(self.document_definitions)
        documents_with_multiple_pages_done = []
        for i, document in enumerate(self.document_definitions):
            # ic(document)
            doc_id = document['name']
            if document['date_start'] == "":
                document['date_start'] = self.inventory["date_start"]
            if document['date_end'] == "":
                document['date_end'] = self.inventory["date_end"]
            if doc_id in documents_with_multiple_pages_done:
                print(
                    f"## {i + 1}/{total_documents} : {doc_id} {document['method']}: {document['title']} (same page range, skipping)")
            else:
                print(f"## {i + 1}/{total_documents} : {doc_id} {document['method']}: {document['title']}")
                ead_hierarchies = self.inventory["hierarchies"]
                ead_identifier_lists = []
                for h in ead_hierarchies:
                    if h["name"] != "EAD":
                        logger.error(f"unexpected hierarchy name: {h["name"]}")
                    else:
                        for p in h["paths"]:
                            identifiers = [e["identifier"] for e in p]
                            ead_identifier_lists.append(identifiers)
                dp = DocumentProcessor(
                    self.inventory_number,
                    doc_id,
                    document,
                    self.preferred_placenames,
                    self.start_data_position,
                    self.end_data_position,
                    self.concept_hierarchies_per_page,
                    self.annotation_enhancements,
                    ead_identifier_lists
                )
                doc = dp.process()
                if doc:
                    self.documents.append(doc)
                    self.annotations_parsed += dp.annotations_parsed
                    self.places_identified += dp.places_identified
                    self.place_annotation_count += dp.place_annotation_count
                    self.professions_identified += dp.professions_identified
                    self.profession_annotation_count += dp.profession_annotation_count
                    self.records_extracted += len(dp.entity_records)
                if document["number_of_scans"] > 1:
                    documents_with_multiple_pages_done.append(doc_id)

        print(f"- documents processed              : {len(self.documents)}")
        print(f"- annotations parsed               : {self.annotations_parsed}")
        print(f"- records extracted                : {self.records_extracted}")
        print(f"- place annotations extracted      : {self.place_annotation_count}")
        print(f"- places identified                : {self.places_identified}")
        print(f"- profession annotations extracted : {self.profession_annotation_count}")
        print(f"- professions identified           : {self.professions_identified}")
        print("")
        self._export()

    def _process_all_pages(self) -> tuple[str, dict[str, int], dict[str, int]]:
        page_ids = self.inventory["documents"][0]["page_ids"]
        logger.info(f"calculating offsets for {len(page_ids)} pages ...")
        start_data_position = {}
        end_data_position = {}
        inventory_text = ""
        inventory_text_data_size = 0
        for i in page_ids:
            transcription_page = self._read_transcription_page(i)
            if transcription_page and "items" in transcription_page:
                items = transcription_page["items"]
                normalized_page_annotation = [i for i in items if i["id"].endswith("#page-normalized")][0]
                if "body" in normalized_page_annotation:
                    normalized_page_text = normalized_page_annotation["body"][0]["value"]
                else:
                    normalized_page_text = ""
                normalized_page_text_bytesize = self._utf8len(normalized_page_text)
                start_data_position[i] = inventory_text_data_size
                end_data_position[i] = inventory_text_data_size + normalized_page_text_bytesize
                inventory_text_data_size += normalized_page_text_bytesize
                inventory_text += normalized_page_text

        return inventory_text, start_data_position, end_data_position

    # Source - https://stackoverflow.com/a/30686735
    # Posted by Kris, modified by community. See post 'Timeline' for change history
    # Retrieved 2026-07-06, License - CC BY-SA 4.0

    @staticmethod
    def _utf8len(s: str) -> int:
        return len(s.encode('utf-8'))

    def _read_transcription_page(self, page_id: str) -> Any:
        transcription_page_path = f"work/{self.inventory_number}/transcriptions/{page_id}.json"
        if os.path.exists(transcription_page_path):
            transcription_page = rw.read_json(transcription_page_path, quiet=True)
        else:
            transcription_page_url = uf.annotation_page_url(AnnotationPageType.TRANSCRIPTIONS, page_id)
            transcription_page = rw.get_json(transcription_page_url, quiet=True)
        return transcription_page

    def _export(self):
        data = self.inventory.copy()
        default_start_date = self.inventory["date_start"]
        default_end_date = self.inventory["date_end"]
        inventory_hierarchy = data.pop("hierarchies")[0]
        # data["documents"] = [self._add_default_dates(d, default_start_date, default_end_date, inventory_hierarchy) for d
        #                      in self.documents]
        data["documents"] = self.documents
        rw.write_json(
            path=f"work/{self.inventory_number}/index.json",
            data=data
        )

        rw.write_text(
            path=f"work/{self.inventory_number}/document.txt",
            text=self.inventory_text
        )

    # @staticmethod
    # def _add_default_dates(document: dict[str, Any], default_start_date: str, default_end_date: str, hierarchy) -> dict[
    #     str, Any]:
    #     if document["start_date"] == "":
    #         document["start_date"] = default_start_date
    #     if document["end_date"] == "":
    #         document["end_date"] = default_end_date
    #     if "hierarchies" in document:
    #         document["hierarchies"].append(hierarchy)
    #     else:
    #         document["hierarchies"] = [hierarchy]
    #     return document

    # def _index_profession_identifiers_per_annotation(self):
    #     self.concept_hierarchies_per_page


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
