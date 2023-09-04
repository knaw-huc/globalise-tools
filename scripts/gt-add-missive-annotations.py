#!/usr/bin/env python3
import csv
import json
import os.path
from typing import Dict, Any

import hydra
from loguru import logger
from omegaconf import DictConfig

import globalise_tools.tools as gt
from globalise_tools.model import WebAnnotation, AnnotationEncoder
from globalise_tools.tools import WebAnnotationFactory

missiven = 'data/generale_missiven.csv'


def as_metadata(missive_record: Dict[str, Any]) -> Dict[str, Any]:
    metadata = {}
    for key in missive_record.keys():
        # namespace = "gl:"
        namespace = ""
        new_key = (namespace + key.lower()
                   .replace(' ', '_')
                   .replace('.', '_')
                   .replace(':', '')
                   .replace('?', '')
                   .replace('(', '')
                   .replace(')', '')
                   )
        metadata[new_key] = missive_record[key]
    return metadata


def store_annotations(annotations):
    path = "out/missive_annotations.json"
    logger.debug(f"=> {path}")
    with open(path, "w") as f:
        json.dump(annotations, fp=f, indent=4, ensure_ascii=False, cls=AnnotationEncoder)


@hydra.main(version_base=None)
@logger.catch
def main(cfg: DictConfig) -> None:
    with open(missiven, 'r') as f:
        reader = csv.DictReader(f, delimiter=';')
        missiven_records = [r for r in reader]
    last_inv_nr = None
    last_segment_ranges = None
    webannotation_factory = WebAnnotationFactory(cfg.iiif_mapping_file, cfg.textrepo.base_uri)
    missive_annotations = []
    for mr in missiven_records:
        if mr['Beginscan']:
            inv_nr = mr['Inv.nr. Nationaal Archief (1.04.02)']
            na_file_id = f"NL-HaNA_1.04.02_{inv_nr}"
            first_scan = f"{int(mr['Beginscan']):04d}"
            last_scan = f"{int(mr['Eindscan']):04d}"
            internal_id = f"{na_file_id}_{first_scan}-{last_scan}"
            page_segment_ranges = {}
            if inv_nr == last_inv_nr:
                page_segment_ranges = last_segment_ranges
            else:
                wa_path = f"out/{na_file_id}/web_annotations.json"
                web_annotations_exist = os.path.exists(wa_path)
                # print(internal_id, wa_path, web_annotations_exist)
                if web_annotations_exist:
                    with open(wa_path) as f:
                        annotations = json.load(f)
                    page_annotations = [a for a in annotations if a['body']['type'] == 'px:Page']
                    page_segment_ranges = {a['body']['metadata']['n']: segment_range(a) for a in page_annotations}
                last_inv_nr = inv_nr
                last_segment_ranges = page_segment_ranges
            if page_segment_ranges:
                first_range = page_segment_ranges[first_scan]
                last_range = page_segment_ranges[last_scan]
                document_range = (first_range[0], first_range[1], last_range[2])
                # print(internal_id, document_range)
                tanap_id = mr['ID in TANAP database']
                # missive_annotation = Annotation(
                #     type="gl:GeneralMissive",

                #
                # )
                segmented_version_id, begin_anchor, end_anchor = document_range

                metadata = as_metadata(mr)

                missive_annotation = WebAnnotation(
                    body={
                        "@context": {"@vocab": "https://knaw-huc.github.io/ns/globalise#"},
                        "id": f"urn:globalise:{na_file_id}:missive:{tanap_id}",
                        "type": "GeneralMissive",
                        "metadata": metadata
                    },
                    target=[
                        webannotation_factory.text_anchor_selector_target(
                            textrepo_base_url=cfg.textrepo.base_uri,
                            segmented_version_id=segmented_version_id,
                            begin_anchor=begin_anchor,
                            end_anchor=end_anchor
                        ),
                        gt.cutout_target(
                            textrepo_base_url=cfg.textrepo.base_uri,
                            segmented_version_id=segmented_version_id,
                            begin_anchor=begin_anchor,
                            end_anchor=end_anchor
                        )
                    ]
                )
                missive_annotations.append(missive_annotation)

                # print(json.dumps(missive_annotation, indent=4, ensure_ascii=False, cls=AnnotationEncoder))
        store_annotations(missive_annotations)


def segment_range(web_annotation: Dict[str, any]):
    targets = web_annotation['target']
    text_anchor_target = [t for t in targets if t['type'] == 'Text' and 'selector' in t]
    # ic(text_anchor_target, len(text_anchor_target))
    tr_version = text_anchor_target[0]['source'].split('/')[-2]
    range_start = text_anchor_target[0]['selector']['start']
    range_end = text_anchor_target[0]['selector']['end']
    # ic(tr_version, range_start, range_end)
    return tr_version, range_start, range_end


if __name__ == '__main__':
    main()