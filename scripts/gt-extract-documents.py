#!/usr/bin/env python3
import csv
import json
import os
from dataclasses import field, dataclass
from pathlib import Path
from typing import List, Dict, Any

import globalise_tools.tools as gt
import hydra
import pagexml.parser as pxp
from annorepo.client import AnnoRepoClient
from dataclasses_json import dataclass_json
from globalise_tools.model import WebAnnotation, AnnotationEncoder
from loguru import logger
from omegaconf import DictConfig
from pagexml.model.physical_document_model import PageXMLScan
from textrepo.client import TextRepoClient


@dataclass_json
@dataclass
class DocumentMetadata:
    inventory_number: str
    scan_range: str
    scan_start: str
    scan_end: str
    no_of_scans: int
    first_scan_nr: int = field(init=False)
    last_scan_nr: int = field(init=False)
    hana_nr: str = field(init=False)
    external_id: str = field(init=False)
    pagexml_ids: List[str] = field(init=False)

    def __post_init__(self):
        # self.no_of_pages = int(self.no_of_pages)
        self.no_of_scans = int(self.no_of_scans)
        (self.first_scan_nr, self.last_scan_nr) = self._scan_nr_range()
        self.hana_nr = f"NL-HaNA_1.04.02_{self.inventory_number}"
        self.external_id = self._external_id()
        self.pagexml_ids = self._pagexml_ids()

    def _scan_nr_range(self) -> (int, int):
        (first_str, last_str) = self.scan_range.split('-')
        first = int(first_str)
        last = int(last_str)
        return first, last

    def _external_id(self) -> str:
        return f"{self.hana_nr}_{self.first_scan_nr:04d}-{self.last_scan_nr:04d}"

    def _pagexml_ids(self) -> List[str]:
        return [f"{self.hana_nr}_{n:04d}" for n in range(self.first_scan_nr, self.last_scan_nr + 1)]


def create_document_directory(doc: DocumentMetadata) -> str:
    output_directory = f'out/{doc.hana_nr}'
    os.makedirs(output_directory, exist_ok=True)
    return output_directory


def download_pagexml(trc: TextRepoClient, base_dir: str, scan_ids: List[str]) -> List[str]:
    paths = []
    for p in scan_ids:
        page_xml_path = f"{base_dir}/{p}.xml"
        paths.append(page_xml_path)
        if not Path(page_xml_path).is_file():
            pagexml = trc.find_latest_file_contents(p, "pagexml").decode('utf8')
            logger.info(f"=> {page_xml_path}")
            with open(page_xml_path, "w") as f:
                f.write(pagexml)
    return paths


def parse_pagexml(path: str, document_id: str, segment_offset: int) -> (List[str], List[WebAnnotation]):
    lines = []
    annotations = []
    logger.debug(f"<= {path}")
    scan_doc: PageXMLScan = pxp.parse_pagexml_file(path)
    id_prefix = gt.make_id_prefix(scan_doc)
    px_text_regions, px_text_lines, px_words = gt.extract_px_elements(scan_doc)
    page_id = to_base_name(path)

    tr_segment_offset = segment_offset
    for text_region in px_text_regions:
        annotations.append(
            gt.text_region_annotation(text_region, id_prefix, tr_segment_offset, text_region.segment_length)
        )
        tr_segment_offset += text_region.segment_length

    tl_segment_offset = segment_offset
    for text_line in px_text_lines:
        lines.append(text_line.text)
        annotations.append(
            gt.text_line_annotation(text_line, id_prefix, tl_segment_offset, 1)
        )
        tl_segment_offset += 1

    annotations.append(
        gt.page_annotation(id_prefix, page_id, path, tl_segment_offset, document_id)
    )

    return lines, annotations


def to_base_name(path: str) -> str:
    return path.split('/')[-1].replace(".xml", "")


def parse_pagexmls(
        pagexml_paths: List[str],
        doc_id: str,
        waf: gt.WebAnnotationFactory
) -> (Dict[str, Any], List[WebAnnotation]):
    document_lines = []
    document_annotations = []
    for path in pagexml_paths:
        lines, annotations = parse_pagexml(path, doc_id, len(document_lines))
        document_lines.extend(lines)
        document_annotations.extend(annotations)
    segmented_text = {"_ordered_segments": document_lines}
    web_annotations = [gt.to_web_annotation(a, waf) for a in document_annotations]
    return segmented_text, web_annotations


def store_segmented_text(base_dir: str, segmented_text: Dict[str, Any]) -> str:
    path = f"{base_dir}/textstore.json"
    logger.debug(f"=> {path}")
    with open(path, 'w') as f:
        json.dump(segmented_text, fp=f, indent=4, ensure_ascii=False)
    return path


def store_annotations(base_dir: str, web_annotations: List[WebAnnotation]) -> str:
    path = f"{base_dir}/web_annotations.json"
    logger.debug(f"=> {path}")
    with open(path, 'w') as f:
        json.dump(web_annotations, fp=f, indent=4, cls=AnnotationEncoder, ensure_ascii=False)
    return path


def upload_segmented_text(trc: TextRepoClient, text_store_path: str):
    logger.warning(f"TODO: upload {text_store_path} to {trc.base_uri}")


def upload_annotations(arc: AnnoRepoClient, annotations_path: str):
    logger.warning(f"TODO: upload {annotations_path} to {arc.base_url}")


def process_document(doc: DocumentMetadata, trc: TextRepoClient, arc: AnnoRepoClient, waf: gt.WebAnnotationFactory):
    base_dir = create_document_directory(doc)
    pagexml_paths = download_pagexml(trc, base_dir, doc.pagexml_ids)
    segmented_text, web_annotations = parse_pagexmls(pagexml_paths, doc.external_id, waf)
    text_store_path = store_segmented_text(base_dir, segmented_text)
    upload_segmented_text(trc, text_store_path)
    annotations_path = store_annotations(base_dir, web_annotations)
    upload_annotations(arc, annotations_path)


def read_document_metadata(selection_file: str) -> List[DocumentMetadata]:
    logger.info(f"<= {selection_file}")
    with open(selection_file, encoding='utf8') as f:
        reader = csv.DictReader(f)
        metadata = [to_document_metadata(row) for row in reader]
    return metadata


def to_document_metadata(rec: Dict[str, any]) -> DocumentMetadata:
    na_base_id = rec['na_base_id']
    start_scan = int(rec['start_scan'])
    end_scan = int(rec['end_scan'])
    inventory_number = na_base_id.split('_')[-1]
    return DocumentMetadata(
        inventory_number=inventory_number,
        scan_range=f'{start_scan}-{end_scan}',
        scan_start=f'https://www.nationaalarchief.nl/onderzoeken/archief/1.04.02/invnr/{inventory_number}/file/{na_base_id}_{start_scan:04d}',
        scan_end=f'https://www.nationaalarchief.nl/onderzoeken/archief/1.04.02/invnr/{inventory_number}/file/{na_base_id}_{end_scan:04d}',
        no_of_scans=end_scan - start_scan + 1
    )


@hydra.main(version_base=None)
@logger.catch
def main(cfg: DictConfig) -> None:
    meta_path = "data/metadata_1618-1793_2022-08-30.csv"

    metadata = read_document_metadata(cfg.documents_file)
    missive_data = gt.read_missive_metadata(meta_path)

    textrepo_client = TextRepoClient(cfg.textrepo.base_uri, api_key=cfg.textrepo.api_key, verbose=False)
    annorepo_client = AnnoRepoClient(cfg.annorepo.base_uri)
    webannotation_factory = gt.WebAnnotationFactory(cfg.iiif_mapping_file)

    with textrepo_client as trc, annorepo_client as arc:
        for dm in metadata[0:1]:
            process_document(dm, trc, arc, webannotation_factory)


if __name__ == '__main__':
    main()
