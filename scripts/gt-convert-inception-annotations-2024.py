#!/usr/bin/env python3
import csv
import json
import os.path
from typing import Dict, Any

import hydra
from icecream import ic
from loguru import logger
from omegaconf import DictConfig

import globalise_tools.tools as gt
from globalise_tools.model import WebAnnotation, AnnotationEncoder
from globalise_tools.tools import WebAnnotationFactory


# metadata_path = "data/document_metadata.csv"


def as_metadata(record: Dict[str, Any]) -> Dict[str, Any]:
    metadata = {"@context": {"gl": "https://knaw-huc.github.io/ns/globalise#"}, "type": "DocumentMetadata"}

    for key in record.keys():
        namespace = "gl:"
        new_key = f"{namespace}{key}"
        metadata[new_key] = record[key]
    return metadata


def store_annotations(annotations):
    path = "out/inception_annotations.json"
    logger.debug(f"=> {path}")
    with open(path, "w") as f:
        json.dump(annotations, fp=f, indent=4, ensure_ascii=False, cls=AnnotationEncoder)


@hydra.main(version_base=None)
@logger.catch
def main(cfg: DictConfig) -> None:
    with open(cfg.selection_file, 'r') as f:
        reader = csv.DictReader(f)
        metadata_records = [r for r in reader if r['Quality Check'] == 'TRUE']
    last_inv_nr = None
    last_segment_ranges = None
    webannotation_factory = WebAnnotationFactory(cfg.iiif_mapping_file, cfg.textrepo.base_uri)
    inception_annotations = []
    total = len(metadata_records)
    for i, mr in enumerate(metadata_records):
        logger.info(f"processing {mr['internal_id']} ({i + 1}/{total})")
        if mr['scan_range']:
            start, end = mr['scan_range'].split('-')
            inv_nr = mr['inventory_number']
            na_file_id = f"NL-HaNA_1.04.02_{inv_nr}"
            first_scan = f"{int(start):04d}"
            last_scan = f"{int(end):04d}"
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
                else:
                    logger.warning(f"file not found: {wa_path} ; skipping this record")
                last_inv_nr = inv_nr
                last_segment_ranges = page_segment_ranges
            if page_segment_ranges:
                first_range = page_segment_ranges[first_scan]
                last_range = page_segment_ranges[last_scan]
                document_range = (first_range[0], first_range[1], last_range[2])
                segmented_version_id, begin_anchor, end_anchor = document_range

                metadata = as_metadata(mr)

                missive_annotation = WebAnnotation(
                    body={
                        "@context": {"@vocab": "https://knaw-huc.github.io/ns/globalise#"},
                        "id": f"urn:globalise:document:{mr['document_id']}",
                        "type": "Document",
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
                    ],
                    custom={
                        "generator": {
                            "id": "https://github.com/brambg/globalise-tools/blob/main/scripts/gt-convert-inception-annotations.py",
                            "type": "Software"}
                    }
                )
                inception_annotations.append(missive_annotation)

                # print(json.dumps(missive_annotation, indent=4, ensure_ascii=False, cls=AnnotationEncoder))
                store_annotations(inception_annotations)


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
