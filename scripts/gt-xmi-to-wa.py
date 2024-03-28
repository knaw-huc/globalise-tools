#!/usr/bin/env python3
import argparse
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Any

import cassis as cas
from loguru import logger

ner_data_dict = {
    'CMTY_NAME': {'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/CMTY_NAME',
                  'label': 'Name of Commodity'},
    'CMTY_QUAL': {'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/CMTY_QUAL',
                  'label': 'Commodity qualifier: colors, processing'},
    'CMTY_QUANT': {'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/CMTY_QUANT',
                   'label': 'Quantity'},
    'DATE': {'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/DATE',
             'label': 'Date'},
    'DOC': {'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/DOC',
            'label': 'Document'},
    'ETH_REL': {'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/ETH_REL',
                'label': 'Ethno-religious appelation or attribute, not derived from location name'},
    'LOC_ADJ': {'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/LOC_ADJ',
                'label': 'Derived (adjectival) form of location name'},
    'LOC_NAME': {'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/LOC_NAME',
                 'label': 'Name of Location'},
    'ORG': {'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/ORG',
            'label': 'Organisation name'},
    'PER_ATTR': {'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/PER_ATTR',
                 'label': 'Other persons attributes (than PER or STATUS)'},
    'PER_NAME': {'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/PER_NAME',
                 'label': 'Name of Person'},
    'PRF': {'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/PRF',
            'label': 'Profession, title'},
    'SHIP': {'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/SHIP',
             'label': 'Ship name'},
    'SHIP_TYPE': {'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/SHIP_TYPE',
                  'label': 'Ship type'},
    'STATUS': {'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/STATUS',
               'label': '(Civic) status'}}


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
        source_list = [d['plain_text_source'] for d in document_data.values() if d['plain_text_md5'] == md5]
        if source_list:
            self.plain_text_source = source_list[0]
        else:
            logger.error(f"No document data found for {xmi_path}, using placeholder target source")
            self.plain_text_source = "urn:placeholder"

    def text(self) -> str:
        return self.text

    def get_named_entity_annotations(self):
        return [self._as_web_annotation(a) for a in self.cas.views[0].get_all_annotations() if
                a.type.name == "de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity" and a.value]
        # return [a for a in cas.views[0].get_all_annotations() if a.type.name=="de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity"]

    def _get_prefix(self, a) -> str:
        extended_prefix_begin = max(0, a.begin - self.max_fix_len * 2)
        extended_prefix = self.text[extended_prefix_begin:a.begin].lstrip().replace('\n', ' ')
        first_space_index = extended_prefix.rfind(' ', 0, self.max_fix_len)
        if first_space_index != -1:
            prefix = extended_prefix[first_space_index + 1:]
        else:
            prefix = extended_prefix
        return prefix

    def _get_suffix(self, a) -> str:
        extended_suffix_end = min(self.text_len, a.end + self.max_fix_len * 2)
        extended_suffix = self.text[a.end:extended_suffix_end].rstrip().replace('\n', ' ')
        last_space_index = extended_suffix.rfind(' ', 0, self.max_fix_len)
        if last_space_index != -1:
            suffix = extended_suffix[:last_space_index]
        else:
            suffix = extended_suffix
        return suffix

    def _as_web_annotation(self, nea):
        anno_id = f"urn:globalise:annotation:{nea.xmiID}"
        text_quote_selector = {
            "type": "TextQuoteSelector",
            "exact": nea.get_covered_text()
        }
        prefix = self._get_prefix(nea)
        if prefix:
            text_quote_selector['prefix'] = prefix
        suffix = self._get_suffix(nea)
        if suffix:
            text_quote_selector['suffix'] = suffix
        entity_id = nea.value
        ner_data = ner_data_dict[entity_id]
        entity_uri = ner_data['uri']
        entity_label = ner_data['label']
        return {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "id": anno_id,
            "type": "Annotation",
            "generated": datetime.today().isoformat(),
            "body": [
                {
                    "type": "SpecificResource",
                    "purpose": "classifying",
                    "source": {
                        "id": entity_uri,
                        "label": entity_label
                    }
                # },
                # {
                #     "purpose": "identifying",
                #
                }
            ],
            "target": {
                "source": self.plain_text_source,
                "selector": [
                    text_quote_selector,
                    {
                        "type": "TextPositionSelector",
                        "start": nea.begin,
                        "end": nea.end
                    }
                ]
            }
        }


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
        basename = xmi_path.split('/')[-1].replace('.xmi', '')
        xp = xpf.get_xmi_processor(xmi_path)

        txt_path = f"{output_dir}/{basename}_plain-text.txt"
        logger.info(f"=> {txt_path}")
        with open(txt_path, 'w') as f:
            f.write(xp.text)

        nea = xp.get_named_entity_annotations()
        json_path = f"{output_dir}/{basename}_web-annotations.json"
        logger.info(f"=> {json_path}")
        with open(json_path, 'w') as f:
            json.dump(nea, f)


if __name__ == '__main__':
    args = get_arguments()
    if args.xmi_path:
        extract_web_annotations(args.xmi_path, args.type_system, args.output_dir)
