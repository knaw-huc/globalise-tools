import json
import sys
from pathlib import Path

from loguru import logger

import scripts.gt_ner_xmi_to_wa as nx
from globalise_tools.pagexml_tools import AnnotationPageBuilder
from scripts.gt_ner_xmi_to_wa import XMIProcessorFactory


class AnnotationPageFactory:
    def __init__(self, inventory_number: str, pagexml_dir: str, xmi_dir: str,
                 xmi_processor_factory: nx.XMIProcessorFactory, manifest_path: str) -> None:
        self.inventory_number = inventory_number
        self.pagexml_dir = pagexml_dir
        self.xmi_dir = xmi_dir
        self.entity_pages = {}
        self.transcription_pages = {}
        self.xmi_processor_factory = xmi_processor_factory
        self._load_manifest(manifest_path)

    def build_annotation_pages(self) -> None:
        for pagexml_path in sorted(Path(self.pagexml_dir).glob("*.xml")):
            page_id = pagexml_path.name.split("/")[-1].replace(".xml", "")
            xmi_path = Path(f"{self.xmi_dir}/{page_id}.xmi")
            dp = DocumentPageProcessor(
                page_id=page_id,
                pagexml_path=pagexml_path,
                xmi_path=xmi_path,
                xpf=self.xmi_processor_factory,
                iiif_base_uri_idx=self.iiif_base_uri_idx,
                canvas_id_idx=self.canvas_id_idx
            )
            self.transcription_pages[page_id] = dp.transcription_annotation_page
            if dp.entity_annotation_page:
                self.entity_pages[page_id] = dp.entity_annotation_page

    def _load_manifest(self, manifest_path: str) -> None:
        logger.info(f"<= {manifest_path}")
        with open(manifest_path) as f:
            manifest = json.load(f)
        self.manifest_item_idx, self.iiif_base_uri_idx, self.canvas_id_idx = nx.index_manifest_items(manifest)


class DocumentPageProcessor:

    def __init__(self, page_id: str, pagexml_path: Path, xmi_path: Path, xpf: XMIProcessorFactory,
                 iiif_base_uri_idx, canvas_id_idx) -> None:
        self.page_id = page_id
        self.pagexml_path = pagexml_path
        self.xmi_path = xmi_path
        xml_string = self._read_page_xml(pagexml_path)
        self.annotation_page_builder = AnnotationPageBuilder(xml_string=xml_string, commit_id=xpf.commit_id)
        self.transcription_annotation_page = {}
        self.entity_annotation_page = None

        if xmi_path.exists():
            htr_word_offsets = self.annotation_page_builder.htr_word_offsets
            logger.info(f"<= {xmi_path}")
            # plain_text_source = nx.handle_page_xml(xmi_path.name, pagexml_path.name, xpf, iiif_base_uri_idx,
            #                                        canvas_id_idx)

            self.entity_annotation_page = {"x": 1}

    @staticmethod
    def _read_page_xml(pagexml_path: Path) -> str:
        try:
            logger.info(f"<= {pagexml_path}")
            with open(pagexml_path, "r", encoding="utf-8") as f:
                xml_string = f.read()
        except FileNotFoundError:
            logger.error(f"Input file not found: {pagexml_path}")
            sys.exit(1)
        return xml_string
