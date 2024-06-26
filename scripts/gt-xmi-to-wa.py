#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
import uuid
from datetime import datetime
from typing import List, Dict, Any, Tuple

import cassis as cas
from cassis.typesystem import FeatureStructure
from intervaltree import IntervalTree, Interval
from loguru import logger

ner_data_dict = {
    'CMTY_NAME': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/CMTY_NAME',
        'label': 'Name of Commodity',
        'entity_type': 'urn:globalise:entityType:Commodity'
    },
    'CMTY_QUAL': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/CMTY_QUAL',
        'label': 'Commodity qualifier: colors, processing',
        'entity_type': 'urn:globalise:entityType:CommodityQualifier'
    },
    'CMTY_QUANT': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/CMTY_QUANT',
        'label': 'Quantity',
        'entity_type': 'urn:globalise:entityType:CommodityQuantity'
    },
    'DATE': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/DATE',
        'label': 'Date',
        'entity_type': 'urn:globalise:entityType:Date'
    },
    'DOC': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/DOC',
        'label': 'Document',
        'entity_type': 'urn:globalise:entityType:Document'
    },
    'ETH_REL': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/ETH_REL',
        'label': 'Ethno-religious appelation or attribute, not derived from location name',
        'entity_type': 'urn:globalise:entityType:EthnoReligiousAppelation'
    },
    'LOC_ADJ': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/LOC_ADJ',
        'label': 'Derived (adjectival) form of location name',
        'entity_type': 'urn:globalise:entityType:Location'
    },
    'LOC_NAME': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/LOC_NAME',
        'label': 'Name of Location',
        'entity_type': 'urn:globalise:entityType:Location'
    },
    'ORG': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/ORG',
        'label': 'Organisation name',
        'entity_type': 'urn:globalise:entityType:Organisation'
    },
    'PER_ATTR': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/PER_ATTR',
        'label': 'Other persons attributes (than PER or STATUS)',
        'entity_type': 'urn:globalise:entityType:PersonAttribute'
    },
    'PER_NAME': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/PER_NAME',
        'label': 'Name of Person',
        'entity_type': 'urn:globalise:entityType:Person'
    },
    'PRF': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/PRF',
        'label': 'Profession, title',
        'entity_type': 'urn:globalise:entityType:Profession'
    },
    'SHIP': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/SHIP',
        'label': 'Ship name',
        'entity_type': 'urn:globalise:entityType:Ship'
    },
    'SHIP_TYPE': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/SHIP_TYPE',
        'label': 'Ship type',
        'entity_type': 'urn:globalise:entityType:Ship'
    },
    'STATUS': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/STATUS',
        'label': '(Civic) status',
        'entity_type': 'urn:globalise:entityType:CivicStatus'
    }
}

wiki_base = "https://github.com/globalise-huygens/nlp-event-detection/wiki#"


class XMIProcessor:
    max_fix_len = 20

    def __init__(self, typesystem, document_data, xmi_path: str):
        self.typesystem = typesystem
        self.document_data = document_data
        self.xmi_path = xmi_path
        logger.info(f"<= {xmi_path}")
        with open(xmi_path, 'rb') as f:
            self.cas = cas.load_cas_from_xmi(f, typesystem=self.typesystem)
        self.text = self.cas.get_sofa().sofaString
        self.text_len = len(self.text)
        md5 = hashlib.md5(self.text.encode()).hexdigest()
        data = None
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
            logger.error(f"No document data found for {xmi_path}, using placeholder target source")
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
            entity_type = ner_data_dict[a['value']]['entity_type']
            web_annotations.append(self._entity_inference_annotation(web_annotation, entity_type, a.xmiID))
        return web_annotations

    def get_event_annotations(self):
        event_annotations = [a for a in self.cas.views[0].get_all_annotations() if
                             a.type.name == "webanno.custom.SemPredGLOB"]
        web_annotations = []
        for event_annotation in event_annotations:
            event_web_annotation = self._as_web_annotation(event_annotation,
                                                           self._event_predicate_body(event_annotation))
            web_annotations.append(event_web_annotation)
            argument_annotations = []
            if event_annotation['arguments']:
                for argument_annotation in event_annotation['arguments']['elements']:
                    argument_annotations.append(argument_annotation)
                    event_argument_web_annotation = \
                        self._as_web_annotation(argument_annotation, self._event_argument_body(argument_annotation))
                    raw_target_entity = event_argument_web_annotation['target'][0]['selector'][0]['exact']
                    target_entity = re.sub(r"[^a-z0-9]+", "_", raw_target_entity.lower()).strip("_")
                    self.event_argument_entity_dict[argument_annotation.xmiID] = target_entity

                    web_annotations.append(event_argument_web_annotation)
                    web_annotations.append(
                        self._event_link_web_annotation(
                            f"{wiki_base}{argument_annotation['role']}",
                            event_web_annotation['id'],
                            event_argument_web_annotation['id']
                        )
                    )
            web_annotations.append(self._event_inference_annotation(event_web_annotation, event_annotation))

        return web_annotations

    def get_event_argument_annotations(self):
        return [self._as_web_annotation(a, self._event_argument_body(a))
                for a in self.cas.views[0].get_all_annotations()
                if a.type.name == "webanno.custom.SemPredGLOBArgumentsLink"]

    def _get_prefix(self, a) -> str:
        extended_prefix_begin = max(0, a['begin'] - self.max_fix_len * 2)
        extended_prefix = self.text[extended_prefix_begin:a['begin']].lstrip().replace('\n', ' ')
        first_space_index = extended_prefix.rfind(' ', 0, self.max_fix_len)
        if first_space_index != -1:
            prefix = extended_prefix[first_space_index + 1:]
        else:
            prefix = extended_prefix
        return prefix

    def _get_suffix(self, a) -> str:
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
        if not feature_structure['begin']:
            feature_structure = feature_structure['target']
        text_quote_selector = {
            "type": "TextQuoteSelector",
            "exact": feature_structure.get_covered_text()
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
        if len(overlapping_intervals) > 1:
            logger.warning(">1 overlapping intervals!")
        for iv in sorted(list(overlapping_intervals)):
            iv_begin, iv_end, iv_data = iv
            # logger.info(f"overlapping interval: [{iv_begin},{iv_end}]")
            canvas_id = iv_data["canvas_id"]
            coords = iv_data["coords"]
            manifest_uri = re.sub(r"/canvas/.*$", "", canvas_id)
            xywh = self._to_xywh(coords)
            # iiif_base_uri = iv_data["iiif_base_uri"]
            # targets.append(self._image_target(iiif_base_uri, xywh))
            # targets.append(self._image_selector_target(iiif_base_uri, xywh))
            targets.append(self._canvas_target(canvas_id, xywh, manifest_uri))

        return {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "id": anno_id,
            "type": "Annotation",
            "generated": datetime.today().isoformat(),
            "body": body,
            "target": targets
        }

    @staticmethod
    def _named_entity_body(feature_structure: FeatureStructure):
        entity_id = feature_structure.value
        ner_data = ner_data_dict[entity_id]
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
        category = feature_structure['category'].replace("+", "Plus").replace("-", "Min")
        category_source = f"{wiki_base}{category}"
        relation_type = f"{wiki_base}{feature_structure['relationtype']}"
        return [
            {
                "purpose": "classifying",
                "source": category_source
            },
            {
                "purpose": "classifying",
                "source": relation_type
            }
        ]

    @staticmethod
    def _event_argument_body(feature_structure: FeatureStructure):
        # ic(feature_structure)
        event_argument_source = f"{wiki_base}{feature_structure['role']}"
        return {
            "purpose": "classifying",
            "source": event_argument_source
        }

    def _event_link_web_annotation(
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
            "motivation": "linking",
            "body": {
                "purpose": "classifying",
                "source": body_source
            },
            "target": [event_annotation_uri, argument_annotation_uri]
        }

    @staticmethod
    def _image_target(iiif_base_uri, xywh):
        return {
            "type": "Image",
            "source": f"{iiif_base_uri}/{xywh}/max/0/default.jpg"
        }

    @staticmethod
    def _image_selector_target(iiif_base_uri, xywh):
        return {
            "type": "Image",
            "source": f"{iiif_base_uri}/full/max/0/default.jpg",
            "selector": {
                "type": "FragmentSelector",
                "conformsTo": "http://www.w3.org/TR/media-frags/",
                "value": f"xywh={xywh}"
            }
        }

    @staticmethod
    def _canvas_target(canvas_source: str, xywh: str,
                       manifest_uri: str):
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
            "selector": {
                "type": "FragmentSelector",
                "conformsTo": "http://www.w3.org/TR/media-frags/",
                "value": f"xywh={xywh}"
            }
        }

    @staticmethod
    def _to_xywh(coords: List[Tuple[int, int]]):
        min_x = min([p[0] for p in coords])
        min_y = min([p[1] for p in coords])
        max_x = max([p[0] for p in coords])
        max_y = max([p[1] for p in coords])
        w = max_x - min_x
        h = max_y - min_y
        return f"{min_x},{min_y},{w},{h}"

    def _entity_inference_annotation(self, entity_annotation, entity_type: str, anno_num: any):
        raw_entity_name = entity_annotation["target"][0]['selector'][0]['exact']
        normalized_entity_name = re.sub(r"[^a-z0-9]+", "_", raw_entity_name.lower()).strip("_")
        entity_annotation_id = entity_annotation['id']
        annotation_id = self._annotation_id(uuid.uuid4())
        entity_id = f"{self._entity_id(normalized_entity_name)}:{anno_num}"
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

    def _event_inference_annotation(self, event_predicate_annotation, event_annotation: FeatureStructure):
        annotation_id = self._annotation_id(uuid.uuid4())
        raw_event_name = event_predicate_annotation["target"][0]['selector'][0]['exact']
        normalized_event_name = re.sub(r"[^a-z0-9]+", "_", raw_event_name.lower()).strip("_")
        event_id = self._event_id(f"{normalized_event_name}:{event_annotation.xmiID}")
        event_type = event_predicate_annotation['body'][0]['source']
        event_annotation_id = event_predicate_annotation['id']
        web_anno = {
            "@context": [
                "http://www.w3.org/ns/anno.jsonld",
                {
                    "prov": "http://www.w3.org/ns/prov#",
                    "glob": "https://github.com/globalise-huygens/nlp-event-detection/wiki#",
                    "sem": "http://semanticweb.cs.vu.nl/2009/11/sem/",
                    "hasActor": "sem:hasActor",
                    "Event": "sem:Event",
                    "roleType": {
                        "@id": "sem:roleType",
                        "@type": "@id"
                    },
                    "value": {
                        "@id": "rdf:value",
                        "@type": "@id"
                    },
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
                "wasDerivedFrom": event_annotation_id
            },
            "target": event_annotation_id
        }
        actors = []
        # ic(event_annotation)
        if event_annotation.arguments:
            for arg in event_annotation.arguments.elements:
                # ic(arg, arg.target)
                roleType = f"glob:{arg.role}"
                value_uri = self._entity_id(f"{self.event_argument_entity_dict[arg.xmiID]}:{arg.target.xmiID}")
                actors.append(
                    {
                        "type": "sem:Role",
                        "roleType": roleType,
                        "value": value_uri
                    }
                )
        if actors:
            web_anno['body']['hasActor'] = actors
        return web_anno

    def _annotation_id(self, extra_id: any) -> str:
        return f"urn:globalise:annotation:{self.document_id}:{extra_id}"

    def _event_id(self, extra_id: any) -> str:
        return f"urn:globalise:event:{self.document_id}:{extra_id}"

    def _entity_id(self, extra_id: any) -> str:
        return f"urn:globalise:entity:{self.document_id}:{extra_id}"


class XMIProcessorFactory:

    def __init__(self, typesystem_path: str):
        logger.info(f"<= {typesystem_path}")
        with open(typesystem_path, 'rb') as f:
            self.typesystem = cas.load_typesystem(f)
        self.document_data = self._read_document_data()

    def get_xmi_processor(self, xmi_path: str) -> XMIProcessor:
        return XMIProcessor(self.typesystem, self.document_data, xmi_path)

    @staticmethod
    def _read_document_data() -> Dict[str, Any]:
        path = "data/document_data.json"
        logger.info(f"<= {path}")
        with open(path) as f:
            return json.load(f)


@logger.catch
def get_arguments():
    parser = argparse.ArgumentParser(
        description="Extract Web Annotations from XMI files",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-t",
                        "--type-system",
                        help="The TypeSystem.xml to use",
                        type=str,
                        required=True
                        )
    parser.add_argument("-o",
                        "--output-dir",
                        help="The directory to write the output files in",
                        type=str
                        )
    parser.add_argument("xmi_path",
                        help="The XMI files to use",
                        type=str,
                        nargs='+'
                        )
    return parser.parse_args()


@logger.catch
def extract_web_annotations(xmi_paths: List[str], typesystem_path: str, output_dir: str):
    if not output_dir:
        output_dir = "."
    xpf = XMIProcessorFactory(typesystem_path)
    for xmi_path in xmi_paths:
        basename = xmi_path.split('/')[-1].replace('.xmi', '').replace(' ', "_")
        xp = xpf.get_xmi_processor(xmi_path)

        txt_path = f"{output_dir}/{basename}_plain-text.txt"
        logger.info(f"=> {txt_path}")
        with open(txt_path, 'w') as f:
            f.write(xp.text)

        nea = xp.get_named_entity_annotations()
        eva = xp.get_event_annotations()
        json_path = f"{output_dir}/{basename}_web-annotations.json"
        logger.info(f"=> {json_path}")
        all_web_annotations = (nea + eva)
        # all_web_annotations.sort(key=lambda a: a['target'][0]['selector'][1]['start'])
        with open(json_path, 'w') as f:
            json.dump(all_web_annotations, f)


if __name__ == '__main__':
    args = get_arguments()
    if args.xmi_path:
        extract_web_annotations(args.xmi_path, args.type_system, args.output_dir)
