#!/usr/bin/env python3
import argparse
import sys

import jsonpath_ng
import orjson
from icecream import ic
from loguru import logger
from tqdm import tqdm


def get_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract NER Web Annotations from XMI files",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-v",
                        help="Turn on logging",
                        action="store_true",
                        default=False,
                        dest='verbose'
                        )
    parser.add_argument("-e",
                        "--entities-page",
                        help="The json-ld file containing the entities annotations page",
                        type=str,
                        required=True
                        )
    parser.add_argument("-t",
                        "--transcriptions-page",
                        help="The json-ld file containing the transcription annotations page",
                        type=str,
                        required=True
                        )
    return parser.parse_args()


class PageHandler:

    def __init__(self, entities_page: str, transcriptions_page: str) -> None:
        self.entities_page = self._load(entities_page)
        self.transcriptions_page = self._load(transcriptions_page)

        self.appellative_subject_type_jsonpath_expr = jsonpath_ng.parse("$.body[*].has_appellative_subject.type")
        self.body_label_jsonpath_expr = jsonpath_ng.parse("$.body[*].label")

        transcription_items = self.transcriptions_page["items"]
        line_items = [i for i in transcription_items if self._is_line(i)]
        word_items = [i for i in transcription_items if self._is_word(i)]

        header_region_ids = [i["id"] for i in transcription_items if self._is_header(i)]
        header_line_ids = [i["id"] for i in line_items if self._targets(i, header_region_ids)]
        header_word_ids = [i["id"] for i in word_items if self._targets(i, header_line_ids)]

        signature_region_ids = [i["id"] for i in transcription_items if self._is_signature(i)]
        signature_line_ids = [i["id"] for i in line_items if self._targets(i, signature_region_ids)]
        signature_word_ids = [i["id"] for i in word_items if self._targets(i, signature_line_ids)]

        entity_items = self.entities_page["items"]

        date_items = [i for i in entity_items if self._is_date(i)]
        date_items_in_headers = [i for i in date_items if self._targets(i, header_word_ids)]
        date_items_in_signatures = [i for i in date_items if self._targets(i, signature_word_ids)]
        self._show("Date", date_items_in_headers, date_items_in_signatures)

        place_items = [i for i in entity_items if self._is_place(i)]
        place_items_in_headers = [i for i in place_items if self._targets(i, header_word_ids)]
        place_items_in_signatures = [i for i in place_items if self._targets(i, signature_word_ids)]
        self._show("Place", place_items_in_headers, place_items_in_signatures)

        person_items = [i for i in entity_items if self._is_person(i)]
        person_items_in_headers = [i for i in person_items if self._targets(i, header_word_ids)]
        person_items_in_signatures = [i for i in person_items if self._targets(i, signature_word_ids)]
        self._show("Person", person_items_in_headers, person_items_in_signatures)

    def _is_header(self, item: dict) -> bool:
        return self._has_source_label_value(item, "header")

    def _is_signature(self, item: dict) -> bool:
        return self._has_source_label_value(item, "signature-mark")

    def _is_date(self, item: dict) -> bool:
        as_type = self.appellative_subject_type_jsonpath_expr.find(item)
        if as_type:
            return as_type[0].value == "TimeSpan"
        else:
            return False

    def _is_place(self, item: dict) -> bool:
        as_type = self.appellative_subject_type_jsonpath_expr.find(item)
        if as_type:
            return as_type[0].value == "Place"
        else:
            return False

    def _is_person(self, item: dict) -> bool:
        as_type = self.appellative_subject_type_jsonpath_expr.find(item)
        if as_type:
            return as_type[0].value == "Person"
        else:
            return False

    def _show(self, a_type: str, in_headers: list, in_signatures: list) -> None:
        if in_headers:
            print(f"{a_type} in headers:")
            for item in in_headers:
                print(f"  {self.body_label_jsonpath_expr.find(item)[0].value}")
            print()
        if in_signatures:
            print(f"{a_type} in signatures:")
            for item in in_signatures:
                print(f"  {self.body_label_jsonpath_expr.find(item)[0].value}")
            print()

    @staticmethod
    def _has_source_label_value(item: dict, value: str) -> bool:
        if "body" in item:
            first_body = item["body"][0]
            if "source" in first_body:
                return first_body["source"]["label"] == value
            else:
                return False
        else:
            return False

    @staticmethod
    def _is_line(item: dict) -> bool:
        return item["textGranularity"] == "line"

    @staticmethod
    def _is_word(item: dict) -> bool:
        return item["textGranularity"] == "word"

    @staticmethod
    def _targets(item: dict, expected_target_ids: list[str]) -> bool:
        annotation_targets = [t for t in item["target"] if t["type"] == "Annotation"]
        if annotation_targets:
            annotation_target_id = annotation_targets[0]["id"]
            return annotation_target_id in expected_target_ids
        else:
            ic(item["target"])
            return False

    @staticmethod
    def _load(filename: str) -> dict:
        with open(filename, "r") as f:
            json = f.read()
            return orjson.loads(json)


@logger.catch
def main() -> None:
    args = get_arguments()
    logger.remove()
    if args.verbose:
        # make loguru logger work with tqdm
        logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)
    else:
        logger.add(sink=sys.stderr, level="WARNING")

    if args.entities_page:
        page_handler = PageHandler(args.entities_page, args.transcriptions_page)


if __name__ == '__main__':
    main()

# Ik zou graag een lijstje van alle datums, persoonsnamen en plaatsnamen in headers en signatures willen
# - vind de word ids van words in header of signature
