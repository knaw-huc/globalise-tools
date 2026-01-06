#!/usr/bin/env python3
import argparse
import copy
import glob
import hashlib
import json
import os
import re
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from functools import cache
from itertools import groupby
from multiprocessing import Value
from typing import Tuple, Any, Optional

import cassis as cas
import multiprocess as mp
import pagexml.parser as px
from cassis.typesystem import FeatureStructure
from circuitbreaker import circuit
from icecream import ic
from intervaltree import Interval, IntervalTree
from loguru import logger
from textrepo.client import FileType, TextRepoClient, VersionInfo
from tqdm import tqdm

import globalise_tools.git_tools as git
import globalise_tools.tools as gt
from globalise_tools.events import (NER_DATA_DICT, place_roles, time_roles,
                                    wiki_base)
from globalise_tools.model import ImageData, Offset
from globalise_tools.tools import inv_nr_sort_key

GLOBALISE_TEAM = "https://globalise.huygens.knaw.nl/team/"

THIS_SCRIPT_PATH = "scripts/" + os.path.basename(__file__)

counter = Value('i', 0)
id_counter = Value('i', 1)
total = Value('i', 0)
start_time = Value('f', 0)

# MANIFEST_BASE_URL = "https://brambg.github.io/static-file-server/globalise"
MANIFEST_BASE_URL = "https://globalise-mirador.tt.di.huc.knaw.nl/globalise"
# MANIFEST_BASE_URL = "http://localhost:8000/globalise"
PRESENTATION_VERSION = 3


@dataclass
class Quant:
    value: str
    unit: Optional[str] = None
    unit_name: Optional[str] = None


def show_progress(future) -> None:
    with counter.get_lock():  # Ensure thread-safe increment
        counter.value += 1
        percentage_done = 100 * (counter.value / total.value)
        now = time.perf_counter()
        seconds_since_start = now - start_time.value
        average_time_per_inv = seconds_since_start / counter.value
        eta = total.value * average_time_per_inv
        seconds_remaining = gt.seconds_to_hhmmss(eta - seconds_since_start)
        logger.info(
            f"finished inventory {counter.value}/{total.value} ({percentage_done:.2f}% done); estimated time remaining: {seconds_remaining}")
        # logger.info(f"all circuits closed: {CircuitBreakerMonitor.all_closed()}")


class XMIProcessor:
    max_fix_len = 20

    def __init__(
            self,
            typesystem,
            document_data,
            commit_id: str,
            xmi_path: str,
            offsets_path: str,
            presentation_version: int = 2,
            time_span: dict[str, str] = None
    ) -> None:
        self.time_span = time_span
        self.typesystem = typesystem
        self.document_data = document_data
        self.xmi_path = xmi_path
        self.commit_id = commit_id
        self.presentation_version = presentation_version
        # logger.info(f"<= {xmi_path}")
        with open(xmi_path, 'rb') as f:
            self.cas = cas.load_cas_from_xmi(f, typesystem=self.typesystem)
        self.text = self.cas.get_sofa().sofaString
        self.text_len = len(self.text)
        self.htr_word_offset = self._load_word_offsets(offsets_path)
        md5 = hashlib.md5(self.text.encode()).hexdigest()
        # ic(md5)
        data = None
        path_parts = xmi_path.split('/')
        base_name = path_parts[-1].replace('.xmi', '')

        self.document_id = base_name
        for k, v in document_data.items():
            if v['plain_text_md5'] == md5:
                self.document_id = k
                data = v
        self.event_argument_entity_dict = {}
        # source_list = [d['plain_text_source'] for d in document_data.values() if d['plain_text_md5'] == md5]
        if data:
            self.plain_text_source = data['plain_text_source']
            self.htr_text_source = data['plain_text_source'].replace("page", "page-htr")
            self.itree = IntervalTree([Interval(*iv) for iv in data['text_intervals']])
        else:
            # logger.error(f"No document data found for {xmi_path}, using placeholder target source")
            raise Exception(f"No document data found for {xmi_path}")
            # # todo: create plain_text_source and itree
            # self.plain_text_source = "urn:example:placeholder"
            # self.itree = IntervalTree()

    def text(self) -> str:
        return self.text

    def get_named_entity_annotations(self) -> list:
        entity_annotations = [a for a in self.cas.views[0].get_all_annotations() if
                              a.type.name == "de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity" and a.value]
        web_annotations = []
        for a in entity_annotations:
            named_entity_annotation = self._as_web_annotation(a, self._named_entity_body(a))
            web_annotations.append(named_entity_annotation)
            # ner_data = NER_DATA_DICT[a['value']]
            # entity_type = ner_data['entity_type']
            # body_type = ner_data['body_type']
            # inference_annotation = self._entity_inference_annotation(named_entity_annotation, entity_type, a.xmiID)
            # web_annotations.append(inference_annotation)
        return web_annotations

    def get_iiif_annotations(self) -> list:
        entity_annotations = [a for a in self.cas.views[0].get_all_annotations() if
                              a.type.name == "de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity" and a.value]
        iiif_annotations = []
        for a in entity_annotations:
            entity_type = NER_DATA_DICT[a['value']]['entity_type']
            annotation = self._as_iiif_annotation(a, entity_type, self.presentation_version)
            iiif_annotations.append(annotation)

        event_annotations = [a for a in self.cas.views[0].get_all_annotations() if
                             a.type.name == "webanno.custom.SemPredGLOB"]
        for a in event_annotations:
            annotation = self._as_iiif_annotation(a, f"{a['relationtype']}:{a['category']}", self.presentation_version)
            iiif_annotations.append(annotation)

        return iiif_annotations

    def get_event_annotations(self, entity_ids: list[str]) -> list:
        event_annotations = [a for a in self.cas.views[0].get_all_annotations() if
                             a.type.name == "webanno.custom.SemPredGLOB"]
        web_annotations = []
        for event_annotation in event_annotations:
            event_argument_annotation_ids = []
            event_linking_annotation_ids = []
            event_predicate_body = self._event_predicate_body(event_annotation)
            if event_predicate_body:
                event_web_annotation = self._as_web_annotation(event_annotation, event_predicate_body)
                web_annotations.append(event_web_annotation)
            else:
                event_web_annotation = None

            argument_annotations = []
            if event_annotation['arguments']:
                for argument_annotation in event_annotation['arguments']['elements']:
                    argument_annotations.append(argument_annotation)
                    event_argument_web_annotation = \
                        self._as_web_annotation(argument_annotation, self._event_argument_body())
                    event_argument_annotation_ids.append(event_argument_web_annotation['id'])
                    raw_target_entity = event_argument_web_annotation['target'][0]['selector'][0]['exact']
                    target_entity = re.sub(r"[^a-z0-9]+", "_", raw_target_entity.lower()).strip("_")
                    self.event_argument_entity_dict[argument_annotation.xmiID] = target_entity

                    web_annotations.append(event_argument_web_annotation)
                    if event_web_annotation:
                        link_web_annotation = self._as_event_link_web_annotation(
                            f"{wiki_base}{argument_annotation['role']}",
                            event_web_annotation['id'],
                            event_argument_web_annotation['id'])
                        web_annotations.append(link_web_annotation)
                        event_linking_annotation_ids.append(link_web_annotation['id'])

            if event_web_annotation:
                web_annotations.append(
                    self._event_inference_annotation(
                        event_annotation=event_annotation,
                        event_predicate_annotation=event_web_annotation,
                        event_argument_annotation_ids=event_argument_annotation_ids,
                        event_linking_annotation_ids=event_linking_annotation_ids
                    )
                )

        return web_annotations

    def get_event_argument_annotations(self) -> list:
        return [self._as_web_annotation(a, self._event_argument_body())
                for a in self.cas.views[0].get_all_annotations()
                if a.type.name == "webanno.custom.SemPredGLOBArgumentsLink"]

    def _get_prefix(self, a) -> str:
        if not a:
            return ""
        extended_prefix_begin = max(0, a['begin'] - self.max_fix_len * 2)
        extended_prefix = self.text[extended_prefix_begin:a['begin']].lstrip().replace('\n', ' ')
        first_space_index = extended_prefix.rfind(' ', 0, self.max_fix_len)
        if first_space_index != -1:
            prefix = extended_prefix[first_space_index + 1:]
        else:
            prefix = extended_prefix
        return prefix

    def _get_suffix(self, a) -> str:
        if not a:
            return ""
        extended_suffix_end = min(self.text_len, a['end'] + self.max_fix_len * 2)
        extended_suffix = self.text[a['end']:extended_suffix_end].rstrip().replace('\n', ' ')
        last_space_index = extended_suffix.rfind(' ', 0, self.max_fix_len)
        if last_space_index != -1:
            suffix = extended_suffix[:last_space_index]
        else:
            suffix = extended_suffix
        return suffix

    def _as_web_annotation(self, feature_structure: FeatureStructure, body) -> dict[
        str, list[str | dict[str, str]] | str | list[str]]:
        anno_id = self._annotation_id(feature_structure.xmiID)
        original_fs = feature_structure
        if feature_structure['begin'] is None:
            feature_structure = feature_structure['target']
        if not feature_structure:
            ic(original_fs)
            logger.error("missing feature_structure")
            exact = ""
        else:
            exact = feature_structure.get_covered_text()
        text_quote_selector = {
            "type": "TextQuoteSelector",
            "exact": exact
        }
        prefix = self._get_prefix(feature_structure)
        if prefix:
            text_quote_selector['prefix'] = prefix
        suffix = self._get_suffix(feature_structure)
        if suffix:
            text_quote_selector['suffix'] = suffix
        feature_structure_begin = feature_structure['begin']
        feature_structure_end = feature_structure['end']
        targets = [
            {
                "type": "SpecificResource",
                "source": {
                    "id": self.plain_text_source,
                    "type": ["DigitalObject", "Annotation"]
                },
                "selector": [
                    text_quote_selector,
                    {
                        "type": "TextPositionSelector",
                        "start": feature_structure_begin,
                        "end": feature_structure_end
                    }
                ]
            }
        ]
        overlapping_intervals = self.itree[feature_structure_begin:feature_structure_end]
        # logger.info(f"source interval: [{nea.begin},{nea.end}] {nea.get_covered_text()}")
        # overlap_size = len(overlapping_intervals)
        # if overlap_size > 1:
        #     logger.warning(
        #         f"{overlap_size} overlapping intervals for [{feature_structure_begin}:{feature_structure_end}]!")
        image_data_list = []
        htr_start = 99999999
        htr_end = 0
        for iv in sorted(list(overlapping_intervals)):
            iv_begin, iv_end, iv_data = iv
            # logger.info(f"overlapping interval: [{iv_begin},{iv_end}]")
            canvas_id = iv_data["canvas_id"]
            coords = iv_data["coords"]
            manifest_uri = re.sub(r"/canvas/.*$", "", canvas_id)
            xywh = self._to_xywh(coords)
            iiif_base_uri = iv_data["iiif_base_uri"]
            image_data = ImageData(
                canvas_id,
                iiif_base_uri,
                manifest_uri,
                xywh,
                coords
            )
            image_data_list.append(image_data)

            word_id = iv_data["word_id"]
            htr_start = min(htr_start, self.htr_word_offset[word_id].begin)
            htr_end = max(htr_end, self.htr_word_offset[word_id].end)

        if htr_end > 0:
            targets.append({
                "type": "SpecificResource",
                "source": {
                    "id": self.htr_text_source,
                    "type": ["DigitalObject", "Annotation"]
                },
                "selector": [
                    text_quote_selector,
                    {
                        "type": "TextPositionSelector",
                        "start": htr_start,
                        "end": htr_end
                    }
                ]
            })
        else:
            ic(overlapping_intervals, exact, feature_structure_begin, feature_structure_end, self.itree.items())
            # targets.append({
            #     "type": "SpecificResource",
            #     "source": {}
            # })
        grouped_image_data = groupby(image_data_list, key=lambda x: x.canvas_id)
        for canvas_id, image_data_groups in grouped_image_data:
            image_data_list = [i for i in image_data_groups]
            iiif_base_uri = [d.iiif_base_uri for d in image_data_list][0]
            manifest_uri = [d.manifest_uri for d in image_data_list][0]
            xywh = [d.xywh for d in image_data_list]

            targets.extend(self._image_targets(iiif_base_uri, xywh))
            targets.append(self._image_selector_target(iiif_base_uri, xywh))
            targets.append(self._canvas_target(canvas_id, xywh, manifest_uri))

        return {
            "@context": [
                "https://linked.art/ns/v1/linked-art.json",
                "https://ns.huc.knaw.nl/globalise.jsonld",
                "https://objectstore.surf.nl/87435b768620494e8e911c83d1997f24:globalise-data/contexts/aaao.json",
                "http://www.w3.org/ns/anno.jsonld",
                "https://objectstore.surf.nl/87435b768620494e8e911c83d1997f24:globalise-data/contexts/crmdig.json",
                {
                    "gan": "https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/",
                    "iiif": "http://iiif.io/api/presentation/3#"
                }
            ],
            "id": anno_id,
            "type": ["Annotation", "DigitalObject"],
            "created": datetime.today().isoformat(),
            "created_by": self._creator(),
            "motivation": "classifying",
            "body": body,
            "target": targets
        }

    def _as_iiif_annotation(self, feature_structure: FeatureStructure, entity_type: str,
                            presentation_version: int = 2) -> dict[str, object]:
        original_fs = feature_structure
        if feature_structure['begin'] is None:
            feature_structure = feature_structure['target']
        if not feature_structure:
            ic(original_fs)
            logger.error("missing feature_structure")
            text = ""
        else:
            text = feature_structure.get_covered_text()
        feature_structure_begin = feature_structure['begin']
        feature_structure_end = feature_structure['end']
        overlapping_intervals = self.itree[feature_structure_begin:feature_structure_end]
        # logger.info(f"source interval: [{nea.begin},{nea.end}] {nea.get_covered_text()}")
        overlap_size = len(overlapping_intervals)
        # ic(feature_structure_begin, feature_structure_end, overlap_size)
        image_data_list = []
        for iv in sorted(list(overlapping_intervals)):
            iv_begin, iv_end, iv_data = iv
            # logger.info(f"overlapping interval: [{iv_begin},{iv_end}]")
            canvas_id = iv_data["canvas_id"]
            coords = iv_data["coords"]
            manifest_uri = re.sub(r"/canvas/.*$", "", canvas_id)
            xywh = self._to_xywh(coords)
            iiif_base_uri = iv_data["iiif_base_uri"]
            image_data = ImageData(
                canvas_id,
                iiif_base_uri,
                manifest_uri,
                xywh,
                coords
            )
            image_data_list.append(image_data)
        grouped_image_data = groupby(image_data_list, key=lambda x: x.canvas_id)
        manifest_uri = []
        canvas_ids = []
        svg_list = []
        xywh_list = []
        for canvas_id, image_data_groups in grouped_image_data:
            canvas_ids.append(canvas_id)
            image_data_list = [i for i in image_data_groups]
            manifest_uri = [d.manifest_uri for d in image_data_list][0]
            xywh = [d.xywh for d in image_data_list]
            coords = [d.coords for d in image_data_list]
            svg_list.append(self._svg_selector(coords_list=coords, xywh_list=xywh))
            xywh_list.extend(xywh)
        if canvas_ids:
            canvas_url = canvas_ids[0]
        else:
            canvas_url = "TODO"
        if xywh_list:
            xywh = xywh_list[0]
        else:
            xywh = "TODO"
        if svg_list:
            svg = svg_list[0]
        else:
            svg = "TODO"
        if manifest_uri:
            manifest = manifest_uri[0]
        else:
            manifest = "TODO"

        printable_entity_type = entity_type.replace('urn:example:globalise:entityType:', "")
        if presentation_version == 2:
            return self._version_2_annotation(canvas_url, manifest, printable_entity_type, svg, text, xywh)
        elif presentation_version == 3:
            return self._version_3_annotation(canvas_url, printable_entity_type, svg, text)
        else:
            raise Exception(f"unknown presentation_version: {presentation_version}")

    @staticmethod
    def _version_2_annotation(canvas_url, manifest, printable_entity_type, svg, text, xywh) -> dict[
        str, str | list[str] | list[dict[str, str]]]:
        return {
            "@id": f"urn:example:globalise:annotation:{uuid.uuid4()}",
            "@type": "oa:Annotation",
            "motivation": [
                "oa:commenting",
                "oa:Tagging"
            ],
            "on": [
                {
                    "@type": "oa:SpecificResource",
                    "full": canvas_url,
                    "selector": {
                        "@type": "oa:Choice",
                        "default": {
                            "@type": "oa:FragmentSelector",
                            "value": f"xywh={xywh}"
                        },
                        "item": {
                            "@type": "oa:SvgSelector",
                            "value": svg
                        }
                    },
                    "within": {
                        "@id": manifest,
                        "@type": "sc:Manifest"
                    }
                }
            ],
            "resource": [
                {
                    "@type": "dctypes:Text",
                    "format": "text/html",
                    "chars": text
                },
                {
                    "@type": "oa:Tag",
                    "format": "text/html",
                    "chars": printable_entity_type
                }
            ]
        }

    @staticmethod
    def _version_3_annotation(canvas_id, printable_entity_type, svg, text) -> dict[str, str | list | dict[str, object]]:
        body = [
            {
                "type": "TextualBody",
                "language": "nl",
                "value": text
            }
        ]
        for value in printable_entity_type.split(':'):
            body.append({
                "type": "TextualBody",
                "purpose": "tagging",
                "value": value
            })
        return {
            "@context": "http://iiif.io/api/presentation/3/context.json",
            "id": f"urn:example:globalise:annotation:{uuid.uuid4()}",
            "type": "Annotation",
            "motivation": "commenting",
            "body": body,
            "target": {
                "source": canvas_id,
                "selector": {
                    "type": "SvgSelector",
                    "value": svg
                }
            }
        }

    def _creator(self) -> dict[str, str]:
        ts = datetime.today().isoformat()
        return {
            "type": "DigitalMachineEvent",
            "_label": "Creation of Web Annotations from Named Entity output in XMI format, using... etc.",
            "carried_out_by": GLOBALISE_TEAM,
            "timespan": {
                "type": "TimeSpan",
                "end_of_the_begin": ts,
                "begin_of_the_end": ts,
            },
            "used_software_or_firmware": {
                "id": "https://github.com/knaw-huc/globalise-tools/blob/"
                      f"{self.commit_id}"
                      f"/{THIS_SCRIPT_PATH}",
                "type": "Software",
                "name": THIS_SCRIPT_PATH,
            }
        }

    def _generator(self) -> dict[str, str]:
        return {
            "id": "https://github.com/knaw-huc/globalise-tools/blob/"
                  f"{self.commit_id}"
                  f"/{THIS_SCRIPT_PATH}",
            "type": "Software",
            "name": THIS_SCRIPT_PATH
        }

    def _named_entity_body(self, feature_structure: FeatureStructure) -> list:
        entity_id = feature_structure.value
        ner_data = NER_DATA_DICT[entity_id]
        body_type = ner_data['body_type']
        covered_text = feature_structure.get_covered_text()
        if entity_id == "LOC_ADJ":
            aBody = self._as_appellative_status_body(ner_data, covered_text)
            c_data = copy.deepcopy(ner_data)
            c_data['body_type'] = "ClassificatoryStatus"
            c_data['classificatory_subject'] = 'PersistentItem'
            cBody = self._as_classificatory_status_body(c_data, covered_text)
            return [aBody, cBody]
        elif body_type == "AppellativeStatus":
            return [self._as_appellative_status_body(ner_data, covered_text)]
        elif body_type == "ClassificatoryStatus":
            return [self._as_classificatory_status_body(ner_data, covered_text)]
        elif body_type == "Dimension":
            return [self._as_dimension_body(ner_data, covered_text)]
        else:
            raise Exception(f"unknown body_type: {body_type}")

    def _as_appellative_status_body(self, ner_data: dict[str, str], covered_text: str) -> dict[str, object]:
        return self._as_base_ner_body(ner_data, "appellative_status") | {
            "has_appellative_subject": {
                "id": self._new_id(ner_data['appellative_subject']),
                "type": ner_data['appellative_subject'],
                "_label": covered_text
            },
            "ascribes_appellative_relation": {
                "id": "http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by",
                "type": "Type",
                "_label": "P1 is identified by"
            },
            "ascribes_appellation": {
                "type": "Name",
                "content": covered_text
            },
        }

    def _as_classificatory_status_body(self, ner_data: dict[str, str], covered_text: str) -> dict[str, object]:
        return self._as_base_ner_body(ner_data, "classificatory_status") | {
            "has_classificatory_subject": {
                "id": self._new_id(ner_data['classificatory_subject']),
                "type": ner_data['classificatory_subject'],
                "_label": covered_text
            },
            "ascribes_classification_relation": {
                "id": "http://www.cidoc-crm.org/cidoc-crm/P2_has_type",
                "type": "Type",
                "_label": "P2 has type"
            },
        }

    def _as_dimension_body(self, ner_data: dict[str, str], covered_text: str) -> dict[str, object]:
        base = self._as_base_ner_body(ner_data, "dimension")
        parts = covered_text.split()
        if len(parts) > 1:
            quant = self._split_cmty_quant(covered_text)
            return base | {
                "value": quant.value,
                "unit": {
                    "id": f"urn:example:globalise:exchangeunit:{quant.unit_name}",
                    "type": "ExchangeUnit",
                    "_label": quant.unit
                }
            }
        else:
            value = covered_text
            return base | {"value": value}
        # return self._as_base_ner_body(ner_data, "dimension") | {
        #     "value": value
        # }

    @staticmethod
    def _split_cmty_quant(cmty_quant: str) -> Quant:
        parts = cmty_quant.split()

        last_digit_part_index = -1

        # Iterate backwards to find the index of the last word with a digit (0-9) or without alphabet characters
        for i, word in reversed(list(enumerate(parts))):
            if any(char.isdigit() for char in word) or not any(char.isalpha() for char in word):
                last_digit_part_index = i
                break

        # Determine the split point
        if last_digit_part_index == -1:
            # No digits found anywhere in the string
            split_index = 0
        else:
            # The split occurs immediately AFTER the last digit-containing word
            split_index = last_digit_part_index + 1

        # Split the list based on the calculated index
        # Number part: words from the beginning up to the split index (exclusive).
        # This includes any descriptive words that precede the number.
        number_words_final = parts[:split_index]
        # Unit part: words from the split index to the end.
        unit_words_final = parts[split_index:]

        # Join the words back into strings
        number_part_str = " ".join(number_words_final)
        unit_part_str = " ".join(unit_words_final)

        # if not number_part_str:
        #     number_part_str = unit_part_str
        #     unit_part_str = ""

        if not unit_part_str:
            if number_part_str.startswith("ƒ"):
                unit_part_str = "ƒ"
                number_part_str = number_part_str[1:].strip()

            if number_part_str.startswith("rd„s"):
                unit_part_str = "Rijksdaalder"
                number_part_str = number_part_str[4:].strip()

            if number_part_str.startswith("rp„"):
                unit_part_str = "Rupees"
                number_part_str = number_part_str[3:].strip()

        if unit_part_str.lower() == "rd„s":
            unit_part_str = "Rijksdaalder"

        if unit_part_str.lower() == "rp„":
            unit_part_str = "Rupees"

        unit_name = unit_part_str.replace(" ", "-").lower()

        return Quant(number_part_str, unit_part_str, unit_name)

    def _as_base_ner_body(self, ner_data, base_name: str) -> dict[str, object]:
        entity_uri = ner_data['uri']
        entity_label = ner_data['label']
        return {
            "id": self._new_id(base_name),
            "type": ner_data['body_type'],
            "timespan": self.time_span,
            "classified_as": {
                "id": entity_uri,
                "type": "Type",
                "_label": entity_label,
            },
        }

    @staticmethod
    def _named_entity_body0(feature_structure: FeatureStructure) -> list[dict[str, str | dict[str, object]]]:
        entity_id = feature_structure.value
        ner_data = NER_DATA_DICT[entity_id]
        entity_uri = ner_data['uri']
        entity_label = ner_data['label']
        return [
            {
                "type": "SpecificResource",
                "source": {
                    "id": entity_uri,
                    "_label": entity_label
                }
            }
        ]

    @staticmethod
    def _event_predicate_body(feature_structure: FeatureStructure) -> list:
        # ic(feature_structure)
        bodies = []
        raw_category = feature_structure['category']
        if not raw_category:
            logger.warning(f"no category for {feature_structure}")
        else:
            category = raw_category.replace("+", "Plus").replace("-", "Min")
            category_source = f"{wiki_base}{category}"
            bodies.append(
                {
                    "purpose": "classifying",
                    "source": category_source
                }
            )
            relation_type = f"{wiki_base}{feature_structure['relationtype']}"
            bodies.append({
                "purpose": "classifying",
                "source": relation_type
            })
        return bodies

    @staticmethod
    def _event_argument_body() -> dict[str, str]:
        return {
            "purpose": "classifying",
            "source": "https://github.com/globalise-huygens/nlp-event-detection/wiki#EventArgument"
        }

    def _as_event_link_web_annotation(
            self,
            argument_identifier: str,
            event_annotation_uri: str,
            argument_annotation_uri: str
    ) -> dict[str, str]:
        body_source = argument_identifier
        target1_num = event_annotation_uri.split(':')[-1]
        target2_num = argument_annotation_uri.split(':')[-1]
        return {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "id": self._annotation_id(f"{target1_num}-{target2_num}"),
            "type": "Annotation",
            "generated": datetime.today().isoformat(),
            "generator": self._generator(),
            "motivation": "linking",
            "body": {
                "purpose": "classifying",
                "source": body_source
            },
            "target": [event_annotation_uri, argument_annotation_uri]
        }

    @staticmethod
    def _image_targets(iiif_base_uri: str, xywh_list: list[str]) -> list:
        return [
            {
                "type": "DigitalObject",
                "source": f"{iiif_base_uri}/{xywh}/max/0/default.jpg"
            }
            for xywh in xywh_list
        ]

    def _image_selector_target(self, iiif_base_uri: str, xywh_list: list[str]) -> dict[str, list[str] | str | list]:
        selectors = self._fragment_selectors(xywh_list)
        return {
            "type": ["Image", "DigitalObject"],
            "source": f"{iiif_base_uri}/full/max/0/default.jpg",
            "selector": selectors
        }

    def _canvas_target(self, canvas_source: str,
                       xywh_list: list[str],
                       manifest_uri: str) -> dict[str, str | dict[str, str | dict[str, str]] | list]:
        selectors = self._fragment_selectors(xywh_list)
        return {
            "type": "SpecificResource",
            "source": {
                '@context': "http://iiif.io/api/presentation/3/context.json",
                "id": canvas_source,
                "type": "Canvas",
                "partOf": {
                    "id": manifest_uri,
                    "type": "Manifest"
                }
            },
            "selector": selectors
        }

    @staticmethod
    def _fragment_selectors(xywh_list) -> list:
        selectors = []
        for xywh in xywh_list:
            selectors.append(
                {
                    "type": "FragmentSelector",
                    "conformsTo": "http://www.w3.org/TR/media-frags/",
                    "value": f"xywh={xywh}"
                }
            )
        if len(selectors) == 1:
            return selectors[0]
        else:
            return selectors

    @staticmethod
    def _to_xywh(coords: list[Tuple[int, int]]) -> str:
        min_x = min([p[0] for p in coords])
        min_y = min([p[1] for p in coords])
        max_x = max([p[0] for p in coords])
        max_y = max([p[1] for p in coords])
        w = max_x - min_x
        h = max_y - min_y
        return f"{min_x},{min_y},{w},{h}"

    @staticmethod
    def _to_coords(x: int, y: int, w: int, h: int) -> list[Tuple[int, int]]:
        # x, y, w, h = [int(p) for p in xywh.split(',')]
        return [
            (x, y),
            (x + w, y),
            (x + w, y + h),
            (x, y + h)
        ]

    def _svg_selector(self, coords_list: list = None, xywh_list: list[str] = None) -> str:
        path_defs = []
        height = 0
        width = 0
        if coords_list:
            for coords in coords_list:
                height = max(height, max([c[1] for c in coords]))
                width = max(width, max([c[0] for c in coords]))
                path_def = ' '.join([f"L{c[0]} {c[1]}" for c in coords]) + " Z"
                path_def = 'M' + path_def[1:]
                path_defs.append(path_def)
        else:
            for xywh in xywh_list:
                x, y, w, h = [int(p) for p in xywh.split(",")]
                coords = self._to_coords(x, y, w, h)
                height = max(height, h)
                width = max(width, w)
                path_def = ' '.join([f"L{c[0]} {c[1]}" for c in coords]) + " Z"
                path_def = 'M' + path_def[1:]
                path_defs.append(path_def)
        path = f"""<path d="{' '.join(path_defs)}"/>"""
        return f"""<svg height="{height}" width="{width}">{path}</svg>"""

    def _entity_inference_annotation(self, entity_annotation, entity_type: str, anno_num: object) -> dict[
        str, list[str | dict[str, str | dict[str, str]]] | str | dict[str, str]]:
        raw_entity_name = entity_annotation["target"][0]['selector'][0]['exact']
        start = entity_annotation["target"][0]['selector'][1]['start']
        end = entity_annotation["target"][0]['selector'][1]['end']
        normalized_entity_name = re.sub(r"[^a-z0-9]+", "_", raw_entity_name.lower()).strip("_")
        entity_annotation_id = entity_annotation['id']
        annotation_id = self._annotation_id(uuid.uuid4())
        entity_id = self._entity_id(start, end, normalized_entity_name)
        return {
            "@context": [
                "http://www.w3.org/ns/anno.jsonld",
                {
                    "prov": "http://www.w3.org/ns/prov#",
                    "wasDerivedFrom": {
                        "@id": "prov:wasDerivedFrom",
                        "@type": "@id"
                    }
                }
            ],
            "id": annotation_id,
            "type": "Annotation",
            "body": {
                "id": entity_id,
                "type": entity_type,
                "wasDerivedFrom": entity_annotation_id,
                "label": raw_entity_name
            },
            "target": entity_annotation_id
        }

    def _event_inference_annotation(self, event_annotation: FeatureStructure,
                                    event_predicate_annotation,
                                    event_argument_annotation_ids=None,
                                    event_linking_annotation_ids=None) -> dict:
        if event_linking_annotation_ids is None:
            event_linking_annotation_ids = []
        if event_argument_annotation_ids is None:
            event_argument_annotation_ids = []
        annotation_id = self._annotation_id(uuid.uuid4())
        raw_event_name = event_predicate_annotation["target"][0]['selector'][0]['exact']
        normalized_event_name = re.sub(r"[^a-z0-9]+", "_", raw_event_name.lower()).strip("_")
        event_id = self._event_id(f"{normalized_event_name}:{event_annotation.xmiID}")
        event_type = event_predicate_annotation['body'][0]['source']
        event_annotation_id = event_predicate_annotation['id']
        event_sources = [event_annotation_id]
        event_sources.extend(event_argument_annotation_ids)
        event_sources.extend(event_linking_annotation_ids)
        web_anno = {
            "@context": [
                "http://www.w3.org/ns/anno.jsonld",
                {
                    "prov": "http://www.w3.org/ns/prov#",
                    "glob": "https://github.com/globalise-huygens/nlp-event-detection/wiki#",
                    "sem": "http://semanticweb.cs.vu.nl/2009/11/sem/",
                    "hasActor": "sem:hasActor",
                    "hasTime": "sem:hasTime",
                    "hasPlace": "sem:hasPlace",
                    "Event": "sem:Event",
                    "roleType": {
                        "@id": "sem:roleType",
                        "@type": "@id"
                    },
                    # "value": {
                    #     "@id": "rdf:value",
                    #     "@type": "@id"
                    # },
                    "wasDerivedFrom": {
                        "@id": "prov:wasDerivedFrom",
                        "@type": "@id"
                    }
                }
            ],
            "id": annotation_id,
            "type": "Annotation",
            "body": {
                "id": event_id,
                "type": ["Event", event_type],
                "wasDerivedFrom": event_sources
            },
            "target": event_annotation_id
        }
        actor_args = []
        place_args = []
        time_args = []
        # ic(event_annotation)
        if event_annotation.arguments:
            for arg in event_annotation.arguments.elements:
                # ic(arg, arg.target)
                roleType = f"glob:{arg.role}"
                start = arg.target.begin
                end = arg.target.end
                entity_id = self._event_argument_id(start, end, self.event_argument_entity_dict[arg.xmiID])
                entity_label = arg.target.get_covered_text()
                role = {
                    "type": "sem:Role",
                    "roleType": roleType,
                    "value": {
                        "id": entity_id,
                        "label": entity_label
                    }
                }
                if arg.role in time_roles:
                    time_args.append(role)
                elif arg.role in place_roles:
                    place_args.append(role)
                else:
                    actor_args.append(role)
        if actor_args:
            web_anno['body']['hasActor'] = actor_args
        if place_args:
            web_anno['body']['hasPlace'] = place_args
        if time_args:
            web_anno['body']['hasTime'] = time_args
        return web_anno

    def _annotation_id(self, extra_id: object) -> str:
        return f"urn:example:globalise:annotation:{self.document_id}:{extra_id}"

    def _event_id(self, extra_id: object) -> str:
        return f"urn:example:globalise:event:{self.document_id}:{extra_id}"

    def _entity_id(self, start: int, end: int, normalized_label: str) -> str:
        return f"urn:example:globalise:entity:{self.document_id}:{start}-{end}:{normalized_label}"

    def _event_argument_id(self, start: int, end: int, normalized_label: str) -> str:
        return f"urn:example:globalise:event_argument:{self.document_id}:{start}-{end}:{normalized_label}"

    def _new_id(self, id_type: str) -> str:
        return f"urn:example:globalise:{id_type.lower()}:{self._next_id_number():06d}"

    @staticmethod
    def _next_id_number() -> int:
        num = id_counter.value
        id_counter.value += 1
        return num

    @staticmethod
    def _load_word_offsets(offsets_path: str) -> dict[str, Offset]:
        logger.info(f"<= {offsets_path}")
        with open(offsets_path, 'rb') as f:
            items = json.load(f).items()
        return {k: Offset(v['begin'], v['end']) for k, v in items}


class XMIProcessorFactory:

    def __init__(
            self,
            typesystem_path: str,
            word_offsets_dir: str,
            timespan4inventory: dict[str, dict[str, str]]
    ) -> None:
        logger.info(f"<= {typesystem_path}")
        with open(typesystem_path, 'rb') as f:
            self.typesystem = cas.load_typesystem(f)
        self.document_data = self._read_document_data()
        self.commit_id = self._read_current_commit_id()
        self.timespan4inventory = timespan4inventory
        self.word_offsets_dir = word_offsets_dir

    def get_xmi_processor(self, xmi_path: str, presentation_version: int = 2) -> XMIProcessor:
        inv_nr = xmi_path.split('/')[-2]
        page_id = xmi_path.split('/')[-1].replace(".xmi", "")
        timespan = self._time_span(inv_nr)
        offsets_path = f"{self.word_offsets_dir}/{page_id}.json"
        return XMIProcessor(
            self.typesystem,
            self.document_data,
            self.commit_id,
            xmi_path,
            offsets_path,
            time_span=timespan,
            presentation_version=presentation_version
        )

    @cache
    def _time_span(self, inv_nr: str) -> dict[str, str]:
        ts = self.timespan4inventory.get(inv_nr, {})
        return {
            "type": "TimeSpan",
            "end_of_the_begin": ts["end_of_the_begin"],
            "begin_of_the_end": ts["begin_of_the_end"],
        }

    @staticmethod
    def _read_document_data() -> dict[str, object]:
        path = "data/document_data.json"
        logger.info(f"<= {path}")
        with open(path) as f:
            return json.load(f)

    @staticmethod
    def _read_current_commit_id() -> str:
        if git.there_are_uncommitted_changes():
            logger.warning("Uncommitted changes! Do a `git commit` first!")
        return git.read_current_commit_id()


from argparse import Namespace


@logger.catch
def get_arguments() -> Namespace:
    parser = argparse.ArgumentParser(
        description="Extract NER Web Annotations from XMI files",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-x",
                        "--xmi-dir",
                        help="The directory containing the xmi files, grouped by inventory number",
                        type=str,
                        required=True
                        )
    parser.add_argument("-p",
                        "--pagexml-dir",
                        help="The directory containing the pagexml files, grouped by inventory number",
                        type=str,
                        required=True
                        )
    parser.add_argument("-w",
                        "--word-offsets-dir",
                        help="The directory containing the word offset files, one per page",
                        type=str,
                        required=True
                        )
    parser.add_argument("-t",
                        "--type-system",
                        help="The TypeSystem.xml to use",
                        type=str,
                        required=True
                        )
    parser.add_argument("-r",
                        "--text-repo",
                        help="The base url of the textrepo server to use",
                        type=str,
                        required=True
                        )
    parser.add_argument("-k",
                        "--api-key",
                        help="The api-key for the textrepo server",
                        type=str,
                        required=True
                        )
    parser.add_argument("-o",
                        "--output-dir",
                        help="The directory to write the output files in",
                        type=str
                        )
    parser.add_argument("-i",
                        "--inv-nr",
                        help="Process only files from this inventory number",
                        type=str
                        )
    return parser.parse_args()


# def extract_web_annotations(xmi_paths: list[str], typesystem_path: str, output_dir: str):
#     if not output_dir:
#         output_dir = "."
#     xpf = XMIProcessorFactory(typesystem_path)
#     for xmi_path in xmi_paths:
#         basename = xmi_path.split('/')[-1].replace('.xmi', '').replace(' ', "_")
#         xp = xpf.get_xmi_processor(xmi_path)
#
#         txt_path = f"{output_dir}/{basename}_plain-text.txt"
#         logger.info(f"=> {txt_path}")
#         with open(txt_path, 'w') as f:
#             f.write(xp.text)
#
#         nea = xp.get_named_entity_annotations()
#         entity_ids = [a['body']['id'] for a in nea if 'id' in a['body']]
#         eva = xp.get_event_annotations(entity_ids)
#         json_path = f"{output_dir}/{basename}_web-annotations.json"
#         all_web_annotations = (nea + eva)
#         logger.info(f"=> {json_path}")
#         with open(json_path, 'w') as f:
#             json.dump(all_web_annotations, f, indent=2, ensure_ascii=False)


def export_ner_annotations(ner_annotations: list, out_path: str) -> None:
    logger.info(f"=> {out_path}")
    # ic(ner_annotations[456])
    with open(out_path, 'w') as f:
        json.dump(ner_annotations, fp=f, indent=4, ensure_ascii=False)


def export_annotation_list(annotations: list[dict[str, object]], out_path: str, presentation_version: int = 2) -> None:
    list_id = out_path.replace("out/", f"{MANIFEST_BASE_URL}/")
    anno_list = {
        "@context": f"http://iiif.io/api/presentation/{presentation_version}/context.json"
    }
    if presentation_version == 2:
        anno_list["@id"] = list_id
        anno_list["@type"] = "sc:AnnotationList"
        anno_list["resources"] = annotations
    elif presentation_version == 3:
        anno_list["id"] = list_id
        anno_list["type"] = "AnnotationPage"
        anno_list["items"] = annotations
    else:
        raise Exception(f"presentation_version {presentation_version} unknown")

    # logger.info(f"=> {out_path}")
    with open(out_path, 'w') as f:
        json.dump(anno_list, fp=f, indent=4, ensure_ascii=False)


def export_text(page_texts: list[str], out_path: str) -> None:
    logger.info(f"=> {out_path}")
    with open(out_path, 'w') as f:
        f.write("\n".join(page_texts))


NUMBERS = re.compile("[0-9]+")
NO_NUMBERS = re.compile("[^0-9]+")


def number_part(path: str) -> tuple[int, str]:
    last = path.split("/")[-1]
    num_part = re.sub(pattern=NO_NUMBERS, string=last, repl="")
    other_part = re.sub(pattern=NUMBERS, string=last, repl="")
    return int(num_part), other_part


@dataclass
class InventoryProcessingContext:
    xmi_dir: str
    output_dir: str
    pagexml_dir: str
    xpf: XMIProcessorFactory
    trc: TextRepoClient
    plain_text_type: FileType
    presentation_version: int


def load_processed_inventories() -> list[str]:
    path = "out/processed_ner_inv.json"
    if os.path.exists(path):
        logger.info(f"<= {path}")
        with open(path) as f:
            return json.load(f)
    return []


def store_processed_inventories(processed_inventories: list[str]) -> None:
    path = "out/processed_ner_inv.json"
    logger.info(f"=> {path}")
    with open(path, "w") as f:
        json.dump(processed_inventories, fp=f, ensure_ascii=False)


def extract_ner_web_annotations(
        pagexml_dir: str,
        xmi_dir: str,
        word_offsets_dir: str,
        type_system_path: str,
        output_dir: str,
        textrepo_url: str,
        api_key: str,
        inv_nr: str = None
) -> None:
    timespan4inventory = load_timespan_dict()
    # trc = TextRepoClient(textrepo_url, api_key=api_key, verbose=False)
    # plain_text_file_type = tt.get_file_type(trc, 'txt', 'text/plain')
    plain_text_file_type = None
    trc = None
    xmi_dirs = sorted(glob.glob(f"{xmi_dir}/[0-9]*"), key=inv_nr_sort_key)
    if inv_nr is not None:
        xmi_dirs = [x for x in xmi_dirs if x.endswith(f"/{inv_nr}")]

    xpf = XMIProcessorFactory(type_system_path, word_offsets_dir, timespan4inventory)

    total.value = len(xmi_dirs)
    logger.info(f"{total.value} inventories to process...")
    run_in_parallel(output_dir, pagexml_dir, plain_text_file_type, trc, xmi_dirs, xpf)
    # run_sequentially(output_dir, pagexml_dir, plain_text_file_type, trc, xmi_dirs, xpf)
    logger.info("done!")


def load_timespan_dict() -> dict[str, dict[str, str]]:
    path = "data/inventory2timespan.json"
    logger.info(f"<= {path}")
    with open(path) as f:
        return json.load(f)


def run_in_parallel(output_dir: str, pagexml_dir: str, plain_text_file_type, trc, xmi_dirs,
                    xpf) -> None:
    contexts = [
        InventoryProcessingContext(
            xmi_dir,
            output_dir,
            pagexml_dir,
            xpf,
            trc,
            plain_text_file_type,
            PRESENTATION_VERSION
        )
        for xmi_dir in xmi_dirs
    ]
    with mp.Pool(5) as p:
        results = p.map(func=process_inventory, iterable=contexts)
    for result in results:
        logger.info(f"finished {result}")
    # with ThreadPoolExecutor() as executor:
    #     results = executor.map(process_inventory, contexts)
    #     for result in results:
    #         logger.info(f"finished {result}")


def run_sequentially(output_dir, pagexml_dir, plain_text_file_type, trc, xmi_dirs, xpf) -> None:
    start_time.value = time.perf_counter()
    for xmi_dir in xmi_dirs:
        context = InventoryProcessingContext(
            xmi_dir,
            output_dir,
            pagexml_dir,
            xpf,
            trc,
            plain_text_file_type,
            PRESENTATION_VERSION
        )
        process_inventory(context)
        # show_progress(None)


def process_inventory(context: InventoryProcessingContext):
    tic = time.perf_counter()
    xmi_dir = context.xmi_dir
    export_dir = context.output_dir
    pagexml_dir = context.pagexml_dir
    xpf = context.xpf
    trc = context.trc

    inv_nr = xmi_dir.split('/')[-1]
    out_dir = f"{export_dir}/{inv_nr}"
    new_manifest_path = f"{out_dir}/{inv_nr}.json"
    if False and os.path.isfile(new_manifest_path):
        logger.info(f"annotated manifest {new_manifest_path} found, skipping {xmi_dir}")
    else:
        logger.info(f"processing {xmi_dir}...")

        xmi_paths = sorted(glob.glob(f"{xmi_dir}/*.xmi"))

        os.makedirs(f"{out_dir}", exist_ok=True)
        anno_out_path = f"{out_dir}/ner-annotations.json"
        ttl_out_path = f"{out_dir}/ner-annotations.ttl"
        text_out_path = f"{out_dir}/text.txt"
        ner_annotations = []
        page_texts = []
        manifest = load_manifest(inv_nr)
        manifest_item_idx, iiif_base_uri_idx, canvas_id_idx = index_manifest_items(manifest)
        for xmi_path in xmi_paths:
            plain_text_source = handle_page_xml(xmi_path, pagexml_dir, xpf, trc, context.plain_text_type,
                                                iiif_base_uri_idx, canvas_id_idx)
            handle_xmi(xmi_path, ner_annotations, page_texts, xpf, plain_text_source, manifest, manifest_item_idx,
                       context.presentation_version, out_dir)
        manifest['id'] = f"{MANIFEST_BASE_URL}/{inv_nr}/{inv_nr}.json"
        store_manifest(inv_nr, manifest)

        export_ner_annotations(ner_annotations, anno_out_path)
        # export_in_ttl(ner_annotations, anno_out_path)
        export_text(page_texts, text_out_path)
        toc = time.perf_counter()
        logger.info(f"processed all xmi files from {xmi_dir} in {toc - tic:0.2f} seconds")
    show_progress(None)
    return xmi_dir


def index_manifest_items(manifest: dict[str, Any]) -> tuple[dict[str, int], dict[str, str], dict[str, str]]:
    manifest_item_idx = {item["label"]["en"][0]: i for i, item in enumerate(manifest["items"])}
    iiif_base_uri_idx = {item["label"]["en"][0]: item['items'][0]['items'][0]['body']['service'][0]['@id'] for item in
                         manifest["items"]}
    canvas_id_idx = {item["label"]["en"][0]: item['id'] for item in manifest["items"]}
    return manifest_item_idx, iiif_base_uri_idx, canvas_id_idx


def load_manifest(inv_nr: str) -> dict[str, object]:
    manifest_path = f"/Users/bram/workspaces/globalise/manifests/inventories/{inv_nr}.json"
    logger.info(f"<= {manifest_path}")
    with open(manifest_path) as f:
        manifest = json.load(f)
    return manifest


def store_manifest(inv_nr: str, manifest: dict[str, object]) -> None:
    manifest_path = f"out/{inv_nr}/{inv_nr}.json"
    logger.info(f"=> {manifest_path}")
    with open(manifest_path, 'w') as f:
        json.dump(obj=manifest, fp=f, ensure_ascii=False)


def handle_xmi(
        xmi_path: str,
        ner_annotations: list,
        page_texts: list,
        xpf: XMIProcessorFactory,
        plain_text_source: str,
        manifest: dict[str, object],
        manifest_item_idx: dict[str, int],
        presentation_version: int = 2,
        out_dir: str = None,
) -> None:
    xp = xpf.get_xmi_processor(xmi_path=xmi_path, presentation_version=presentation_version)
    page_text = xp.text
    page_texts.append(page_text)
    basename = get_base_name(xmi_path)

    text_path = f"{out_dir}/{basename}.txt"
    # logger.info(f"=> {text_path}")
    with open(text_path, 'w') as f:
        f.write(page_text)

    basename_parts = basename.split("_")
    xp.plain_text_source = plain_text_source
    xp.document_id = basename
    nea = xp.get_named_entity_annotations()
    ner_annotations.extend(nea)
    # entity_ids = [a['body']['id'] for a in nea if 'id' in a['body']]
    # eva = xp.get_event_annotations(entity_ids)
    # ner_annotations.extend(eva)
    inv_nr = basename_parts[-2]
    # annotation_list_path = f"out/{inv_nr}/iiif-annotations-{basename}.json"
    # export_annotation_list(annotations=xp.get_iiif_annotations(), out_path=annotation_list_path,
    #                        presentation_version=presentation_version)
    manifest_items = manifest["items"]
    if basename in manifest_item_idx:
        relevant_item_index = manifest_item_idx[basename]
        manifest_items[relevant_item_index]["annotations"] = [
            {
                "@context": f"http://iiif.io/api/presentation/{presentation_version}/context.json",
                "id": f"{MANIFEST_BASE_URL}/{inv_nr}/iiif-annotations-{basename}.json",
                "type": "AnnotationPage"
            }
        ]
    else:
        logger.warning(f"no canvas entry found in manifest {inv_nr}.json for {basename}")


@circuit(failure_threshold=10, expected_exception=ConnectionError)
def upload_to_textrepo(
        trc: TextRepoClient,
        external_id: str, contents: str,
        plain_text_file_type: FileType
) -> VersionInfo:
    txt_version_identifier = trc.import_version(
        external_id=external_id,
        type_name=plain_text_file_type.name,
        contents=contents,
        as_latest_version=True
    )
    return txt_version_identifier


def get_base_name(path: str):
    return path.split("/")[-1].replace(".xmi", "")


def make_transcription_annotation_page(page_xml_path) -> None:
    pass


def handle_page_xml(
        xmi_path: str,
        pagexml_dir: str,
        xpf: XMIProcessorFactory,
        trc: TextRepoClient,
        plain_text_file_type: FileType,
        iiif_base_uri_for_base_name: dict[str, str],
        canvas_id_for_base_name: dict[str, str]) -> str:
    base_name = get_base_name(xmi_path)
    page_xml_path = get_page_xml_path(xmi_path, pagexml_dir)
    make_transcription_annotation_page(page_xml_path)
    scan_doc = px.parse_pagexml_file(pagexml_file=page_xml_path)
    if base_name in iiif_base_uri_for_base_name:
        iiif_base_uri = iiif_base_uri_for_base_name[base_name]
        canvas_id = canvas_id_for_base_name[base_name]
    else:
        logger.warning(f"base_name {base_name} not found in manifest")
        iiif_base_uri = f"http://canvas-{base_name}-not-found-in-manifest"
        canvas_id = f"http://canvas-{base_name}-not-found-in-manifest"
    text, marginalia_ranges, header_range, paragraph_ranges, word_interval_tree = gt.extract_paragraph_text(scan_doc,
                                                                                                            iiif_base_uri=iiif_base_uri,
                                                                                                            canvas_id=canvas_id)

    plain_text = text
    # txt_version_identifier = upload_to_textrepo(trc, base_name, plain_text, plain_text_file_type)
    # txt_version_uri = f"{trc.base_uri}/rest/versions/{txt_version_identifier.version_id}"
    # txt_version_uri = "urn:example:placeholder"
    plain_text_source = f"https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/annotations:transcriptions:{base_name}#page"

    md5 = hashlib.md5(plain_text.encode()).hexdigest()
    xpf.document_data[base_name] = {
        "plain_text_source": plain_text_source,
        "plain_text_md5": md5,
        "text_intervals": list(word_interval_tree)
    }
    return plain_text_source


def get_page_xml_path(xmi_path: str, pagexml_dir: str) -> str:
    path_parts = xmi_path.split('/')
    xmi_base = path_parts[-1].replace('.xmi', '')
    inv_nr = path_parts[-2]
    return f"{pagexml_dir}/{inv_nr}/{xmi_base}.xml"


@logger.catch
def main() -> None:
    # make loguru logger work with tqdm
    logger.remove()
    logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)
    args = get_arguments()
    if args.xmi_dir:
        extract_ner_web_annotations(args.pagexml_dir, args.xmi_dir, args.word_offsets_dir, args.type_system,
                                    args.output_dir, args.text_repo,
                                    args.api_key, args.inv_nr)


if __name__ == '__main__':
    main()

"""
Om de ner/event annotaties uit de xmi te kunnen mappen op de documenten zoals in tav gebruikt:
- in tav: per inv.nr alle pagexml text achter elkaar, op line nivo voor physical, op para nivo voor logical
- in xmi: per pagexml, voor logical text (met alternatieve afbrekingsoplossing?)

Er moeten verschillende mappings komen:
op logical word nivo -> physical textrepo coords -> pagexml word coords -> xmi text ranges
via de pagexml words?
xmi tokens -> pagexml words -> physical offset -> logical offset


manifest
4085
9524I
9524II
ontbreken

geen ner-annotations:
10179
10467
4069
"""
