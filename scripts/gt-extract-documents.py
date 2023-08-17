#!/usr/bin/env python3
import json
import os
from pathlib import Path
from typing import List, Dict, Any

import hydra
from annorepo.client import AnnoRepoClient
from globalise_tools.model import Document, WebAnnotation
from globalise_tools.tools import read_document_metadata
from loguru import logger
from omegaconf import DictConfig
from textrepo.client import TextRepoClient


def create_document_directory(doc: Document) -> str:
    output_directory = f'out/{doc.hana_id()}'
    os.makedirs(output_directory, exist_ok=True)
    return output_directory


def download_pagexml(trc: TextRepoClient, base_dir: str, scan_ids: List[str]) -> List[str]:
    paths = []
    for p in scan_ids:
        page_xml_path = f"{base_dir}/{p}.xml"
        if not Path(page_xml_path).is_file():
            pagexml = trc.find_latest_file_contents(p, "pagexml").decode('utf8')
            logger.info(f"=> {page_xml_path}")
            with open(page_xml_path, "w") as f:
                f.write(pagexml)
    return paths


def parse_pagexml(pagexml_paths: List[str]) -> (Dict[str, Any], List[WebAnnotation]):
    document_lines = []
    web_annotations = []
    segmented_text = {"_ordered_segments": document_lines}
    return segmented_text, web_annotations


def store_segmented_text(base_dir: str, segmented_text: Dict[str, Any]) -> str:
    path = f"{base_dir}/textstore.json"
    logger.debug(f"=> {path}")
    with open(path, 'w') as f:
        json.dump(segmented_text, fp=f, indent=4)
    return path


def store_annotations(base_dir: str, web_annotations: List[WebAnnotation]) -> str:
    path = f"{base_dir}/web_annotations.json"
    logger.debug(f"=> {path}")
    with open(path, 'w') as f:
        json.dump(web_annotations, fp=f, indent=4)
    return path


def upload_segmented_text(trc: TextRepoClient, text_store_path: str):
    logger.warning(f"TODO: upload {text_store_path} to {trc.base_uri}")


def upload_annotations(arc: AnnoRepoClient, annotations_path: str):
    logger.warning(f"TODO: upload {annotations_path} to {arc.base_url}")


def process_document(doc: Document, trc: TextRepoClient, arc: AnnoRepoClient):
    base_dir = create_document_directory(doc)
    pagexml_paths = download_pagexml(trc, base_dir, doc.scan_ids())
    segmented_text, web_annotations = parse_pagexml(pagexml_paths)
    text_store_path = store_segmented_text(base_dir, segmented_text)
    upload_segmented_text(trc, text_store_path)
    annotations_path = store_annotations(base_dir, web_annotations)
    upload_annotations(arc, annotations_path)


@hydra.main(version_base=None)
@logger.catch
def main(cfg: DictConfig) -> None:
    meta_path = "data/metadata_1618-1793_2022-08-30.csv"

    documents = read_document_metadata(meta_path)

    textrepo_client = TextRepoClient(cfg.textrepo.base_uri, api_key=cfg.textrepo.api_key, verbose=False)
    annorepo_client = AnnoRepoClient(cfg.annorepo.base_uri)

    with textrepo_client as trc, annorepo_client as arc:
        for dm in documents[0:2]:
            process_document(dm, trc, arc)


if __name__ == '__main__':
    main()
