#!/usr/bin/env python3
import argparse
import glob
import hashlib
import json
import os
import re
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from itertools import groupby
from multiprocessing import Value
from typing import Tuple

import cassis as cas
import dask.distributed as dask
import pagexml.parser as px
from cassis.typesystem import FeatureStructure
from icecream import ic
from intervaltree import IntervalTree, Interval
from loguru import logger
from textrepo.client import TextRepoClient, FileType
from tqdm import tqdm

import globalise_tools.git_tools as git
import globalise_tools.textrepo_tools as tt
from globalise_tools.events import wiki_base, time_roles, place_roles, NER_DATA_DICT
from globalise_tools.model import ImageData
from globalise_tools.tools import seconds_to_hhmmss

THIS_SCRIPT_PATH = "scripts/" + os.path.basename(__file__)

counter = Value('i', 0)
total = Value('i', 0)
start_time = Value('f', 0)


def show_progress(future):
    with counter.get_lock():  # Ensure thread-safe increment
        counter.value += 1
        percentage_done = 100 * (counter.value / total.value)
        now = time.perf_counter()
        seconds_since_start = now - start_time.value
        average_time_per_inv = seconds_since_start / counter.value
        eta = total.value * average_time_per_inv
        seconds_remaining = seconds_to_hhmmss(eta - seconds_since_start)
        logger.info(
            f"finished inventory {counter.value}/{total.value} ({percentage_done:.2f}% done); estimated time remaining: {seconds_remaining}")


class XMIProcessor:
    max_fix_len = 20

    def __init__(self, typesystem, document_data, commit_id: str, xmi_path: str):
        self.typesystem = typesystem
        self.document_data = document_data
        self.xmi_path = xmi_path
        self.commit_id = commit_id
        # logger.info(f"<= {xmi_path}")
        with open(xmi_path, 'rb') as f:
            self.cas = cas.load_cas_from_xmi(f, typesystem=self.typesystem)
        self.text = self.cas.get_sofa().sofaString
        self.text_len = len(self.text)
        md5 = hashlib.md5(self.text.encode()).hexdigest()
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
            self.itree = IntervalTree([Interval(*iv) for iv in data['text_intervals']])
        else:
            # logger.error(f"No document data found for {xmi_path}, using placeholder target source")
            # raise Exception(f"No document data found for {xmi_path}")
            # todo: create plain_text_source and itree
            self.plain_text_source = "urn:placeholder"
            self.itree = IntervalTree()

    def text(self) -> str:
        return self.text

    def get_named_entity_annotations(self):
        entity_annotations = [a for a in self.cas.views[0].get_all_annotations() if
                              a.type.name == "de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity" and a.value]
        web_annotations = []
        for a in entity_annotations:
            web_annotation = self._as_web_annotation(a, self._named_entity_body(a))
            web_annotations.append(web_annotation)
            entity_type = NER_DATA_DICT[a['value']]['entity_type']
            web_annotations.append(self._entity_inference_annotation(web_annotation, entity_type, a.xmiID))
        return web_annotations

    def get_event_annotations(self, entity_ids: list[str]):
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

    def get_event_argument_annotations(self):
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

    def _as_web_annotation(self, feature_structure: FeatureStructure, body):
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
                "source": self.plain_text_source,
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
        overlap_size = len(overlapping_intervals)
        if overlap_size > 1:
            logger.warning(
                f"{overlap_size} overlapping intervals for [{feature_structure_begin}:{feature_structure_end}]!")
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
                xywh
            )
            image_data_list.append(image_data)
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
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "id": anno_id,
            "type": "Annotation",
            "generated": datetime.today().isoformat(),
            "generator": self._generator(),
            "body": body,
            "target": targets
        }

    def _generator(self):
        return {
            "id": "https://github.com/knaw-huc/globalise-tools/blob/"
                  f"{self.commit_id}"
                  f"/{THIS_SCRIPT_PATH}",
            "type": "Software",
            "name": THIS_SCRIPT_PATH
        }

    @staticmethod
    def _named_entity_body(feature_structure: FeatureStructure):
        entity_id = feature_structure.value
        ner_data = NER_DATA_DICT[entity_id]
        entity_uri = ner_data['uri']
        entity_label = ner_data['label']
        return [
            {
                "type": "SpecificResource",
                "purpose": "classifying",
                "source": {
                    "id": entity_uri,
                    "label": entity_label
                }
            }
        ]

    @staticmethod
    def _event_predicate_body(feature_structure: FeatureStructure):
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
    def _event_argument_body():
        return {
            "purpose": "classifying",
            "source": "https://github.com/globalise-huygens/nlp-event-detection/wiki#EventArgument"
        }

    def _as_event_link_web_annotation(
            self,
            argument_identifier: str,
            event_annotation_uri: str,
            argument_annotation_uri: str
    ):
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
    def _image_targets(iiif_base_uri: str, xywh_list: list[str]):
        return [
            {
                "type": "Image",
                "source": f"{iiif_base_uri}/{xywh}/max/0/default.jpg"
            }
            for xywh in xywh_list
        ]

    def _image_selector_target(self, iiif_base_uri: str, xywh_list: list[str]):
        selectors = self._fragment_selectors(xywh_list)
        return {
            "type": "Image",
            "source": f"{iiif_base_uri}/full/max/0/default.jpg",
            "selector": selectors
        }

    def _canvas_target(self, canvas_source: str,
                       xywh_list: list[str],
                       manifest_uri: str):
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
    def _fragment_selectors(xywh_list):
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
    def _to_xywh(coords: list[Tuple[int, int]]):
        min_x = min([p[0] for p in coords])
        min_y = min([p[1] for p in coords])
        max_x = max([p[0] for p in coords])
        max_y = max([p[1] for p in coords])
        w = max_x - min_x
        h = max_y - min_y
        return f"{min_x},{min_y},{w},{h}"

    def _entity_inference_annotation(self, entity_annotation, entity_type: str, anno_num: any):
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
                                    event_argument_annotation_ids: list[str] = [],
                                    event_linking_annotation_ids: list[str] = []):
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

    def _annotation_id(self, extra_id: any) -> str:
        return f"urn:globalise:annotation:{self.document_id}:{extra_id}"

    def _event_id(self, extra_id: any) -> str:
        return f"urn:globalise:event:{self.document_id}:{extra_id}"

    def _entity_id(self, start: int, end: int, normalized_label: str) -> str:
        return f"urn:globalise:entity:{self.document_id}:{start}-{end}:{normalized_label}"

    def _event_argument_id(self, start: int, end: int, normalized_label: str) -> str:
        return f"urn:globalise:event_argument:{self.document_id}:{start}-{end}:{normalized_label}"


class XMIProcessorFactory:

    def __init__(self, typesystem_path: str):
        logger.info(f"<= {typesystem_path}")
        with open(typesystem_path, 'rb') as f:
            self.typesystem = cas.load_typesystem(f)
        self.document_data = self._read_document_data()
        self.commit_id = self._read_current_commit_id()

    def get_xmi_processor(self, xmi_path: str) -> XMIProcessor:
        return XMIProcessor(self.typesystem, self.document_data, self.commit_id, xmi_path)

    @staticmethod
    def _read_document_data() -> dict[str, any]:
        path = "data/document_data.json"
        logger.info(f"<= {path}")
        with open(path) as f:
            return json.load(f)

    @staticmethod
    def _read_current_commit_id():
        if git.there_are_uncommitted_changes():
            logger.warning("Uncommitted changes! Do a `git commit` first!")
        return git.read_current_commit_id()


@logger.catch
def get_arguments():
    parser = argparse.ArgumentParser(
        description="Extract NER Web Annotations from XMI files",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-x",
                        "--xmi-dir",
                        help="The directory containing the xmi files, grouped by inventory number",
                        type=str
                        )
    parser.add_argument("-p",
                        "--pagexml-dir",
                        help="The directory containing the pagexml files, grouped by inventory number",
                        type=str
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


def export_ner_annotations(ner_annotations: list, out_path: str):
    logger.info(f"=> {out_path}")
    with open(out_path, 'w') as f:
        json.dump(ner_annotations, fp=f, indent=4)


def export_text(page_texts: list[str], out_path: str):
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
    processed_inventories: list[str]


def load_processed_inventories() -> list[str]:
    path = "out/processed_ner_inv.json"
    if os.path.exists(path):
        logger.info(f"<= {path}")
        with open(path) as f:
            return json.load(f)
    return []


def store_processed_inventories(processed_inventories: list[str]):
    path = "out/processed_ner_inv.json"
    logger.info(f"=> {path}")
    with open(path, "w") as f:
        json.dump(processed_inventories, fp=f)


def extract_ner_web_annotations(pagexml_dir: str, xmi_dir: str, type_system_path: str, output_dir: str,
                                textrepo_url: str, api_key: str):
    trc = TextRepoClient(textrepo_url, api_key=api_key, verbose=False)
    plain_text_file_type = tt.get_file_type(trc, 'txt', 'text/plain')
    # ic(pagexml_dir, xmi_dir, type_system_path, output_dir)
    # pagexml_dirs = sorted(glob.glob(f"{pagexml_dir}/[0-9]*"), key=number_part)
    # xmi_dirs = sorted(glob.glob(f"{xmi_dir}/[0-9]*"), key=number_part)
    xmi_dirs = glob.glob(f"{xmi_dir}/[0-9]*")
    # pagexml_inv_nrs = [p.split('/')[-1] for p in pagexml_dirs]
    # xmi_inv_nrs = [p.split('/')[-1] for p in xmi_dirs]
    xpf = XMIProcessorFactory(type_system_path)
    processed_inventories = load_processed_inventories()

    total.value = len(xmi_dirs)
    logger.info(f"{total.value} inventories to process...")
    client = dask.Client()
    logger.info(f"mapping processes...")
    futures = client.map(process_inventory,
                         [InventoryProcessingContext(xmi_dir, output_dir, pagexml_dir, xpf, trc, plain_text_file_type,
                                                     processed_inventories)
                          for xmi_dir in xmi_dirs[0:5]])
    logger.info("adding callbacks...")
    for future in futures:
        future.add_done_callback(show_progress)

    start_time.value = time.perf_counter()
    logger.info("gathering...")
    client.gather(futures)
    logger.info("done!")


def process_inventory(context: InventoryProcessingContext):
    tic = time.perf_counter()
    xmi_dir = context.xmi_dir
    output_dir = context.output_dir
    pagexml_dir = context.pagexml_dir
    xpf = context.xpf
    trc = context.trc
    processed_inventories = context.processed_inventories

    inv_nr = xmi_dir.split('/')[-1]
    if inv_nr in processed_inventories:
        logger.info(f"skipping {xmi_dir}...")
    else:
        logger.info(f"processing {xmi_dir}...")

        xmi_paths = sorted(glob.glob(f"{xmi_dir}/*.xmi"))
        os.makedirs(f"{output_dir}/{inv_nr}", exist_ok=True)
        anno_out_path = f"{output_dir}/{inv_nr}/ner-annotations.json"
        text_out_path = f"{output_dir}/{inv_nr}/text.txt"
        ner_annotations = []
        page_texts = []
        for xmi_path in xmi_paths:
            handle_page_xml(xmi_path, pagexml_dir, xpf, trc)
            handle_xmi(xmi_path, ner_annotations, page_texts, xpf, trc, context.plain_text_type)

        export_ner_annotations(ner_annotations, anno_out_path)
        export_text(page_texts, text_out_path)
        toc = time.perf_counter()
        logger.info(f"processed all xmi files from {xmi_dir} in {toc - tic:0.2f} seconds")
        # processed_inventories.append(inv_nr)
        # store_processed_inventories(processed_inventories)


def handle_xmi(xmi_path: str, ner_annotations, page_texts, xpf: XMIProcessorFactory, trc: TextRepoClient,
               plain_text_file_type: FileType):
    xp = xpf.get_xmi_processor(xmi_path)
    page_text = xp.text
    page_texts.append(page_text)
    basename = get_base_name(xmi_path)
    txt_version_identifier = trc.import_version(
        external_id=basename,
        type_name=plain_text_file_type.name,
        contents=page_text,
        as_latest_version=True
    )
    xp.document_id = basename
    xp.plain_text_source = trc.version_uri(txt_version_identifier.version_id)
    ner_annotations.extend(xp.get_named_entity_annotations())


def get_base_name(path: str):
    return path.split("/")[-1].replace(".xmi", "")


def handle_page_xml(xmi_path: str, pagexml_dir: str, xpf: XMIProcessorFactory, trc: TextRepoClient):
    base_name = get_base_name(xmi_path)
    page_xml_path = get_page_xml_path(xmi_path, pagexml_dir)
    scan_doc = px.parse_pagexml_file(pagexml_file=page_xml_path)
    raw_text_offset = 0
    raw_text_range = IntervalTree()
    for tr in scan_doc.get_text_regions_in_reading_order():
        for w in tr.get_words():
            new_offset = raw_text_offset + 1 + len(w.text)
            raw_text_range[raw_text_offset:new_offset] = w
            raw_text_offset = new_offset
    # md5 = hashlib.md5(plain_text.encode()).hexdigest()
    # txt_version_uri = f"{trc.base_uri}/rest/versions/{txt_version_identifier.version_id}"
    # xpf.document_data[base_name] = {
    #     "plain_text_source": f"{txt_version_uri}/contents",
    #     "plain_text_md5": md5,
    #     "text_intervals": list(raw_text_range)
    # }


def get_page_xml_path(xmi_path: str, pagexml_dir: str) -> str:
    path_parts = xmi_path.split('/')
    xmi_base = path_parts[-1].replace('.xmi', '')
    inv_nr = path_parts[-2]
    return f"{pagexml_dir}/{inv_nr}/{xmi_base}.xml"


@logger.catch
def main():
    # make loguru logger work with tqdm
    logger.remove()
    logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)
    args = get_arguments()
    if args.xmi_dir:
        extract_ner_web_annotations(args.pagexml_dir, args.xmi_dir, args.type_system, args.output_dir, args.text_repo,
                                    args.api_key)


if __name__ == '__main__':
    main()
