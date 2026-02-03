import json
import sys
from pathlib import Path
from typing import Any

import multiprocess as mp
from loguru import logger

import globalise_tools.pagexml_tools as pt
import globalise_tools.url_factory as uf
import scripts.gt_ner_xmi_to_wa as nx
from scripts.gt_ner_xmi_to_wa import XMIProcessorFactory


class AnnotationPageFactory:
    def __init__(self, inventory_number: str, pagexml_dir: str, xmi_dir: str,
                 xmi_processor_factory: nx.XMIProcessorFactory, manifest_path: str, script_path: str) -> None:
        self.inventory_number = inventory_number
        self.pagexml_dir = pagexml_dir
        self.xmi_dir = xmi_dir
        self.entity_pages = {}
        self.transcription_pages = {}
        self.xmi_processor_factory = xmi_processor_factory
        self.script_path = script_path
        self._load_manifest(manifest_path)

    def build_annotation_pages(self) -> None:
        pagexml_paths = sorted(Path(self.pagexml_dir).glob("*.xml"))
        # self._run_in_parallel(pagexml_paths)
        self._run_sequentially(pagexml_paths)

    def _run_in_parallel(self, pagexml_paths: list[Path], pool_size: int = 5):
        with mp.Pool(pool_size) as p:
            results = p.map(func=self._process_pagexml, iterable=pagexml_paths)
        for page_id, transcription_annotation_page, entity_annotation_page in results:
            self.transcription_pages[page_id] = transcription_annotation_page
            if entity_annotation_page:
                self.entity_pages[page_id] = entity_annotation_page

    def _run_sequentially(self, pagexml_paths: list[Path]):
        for pagexml_path in pagexml_paths:
            page_id, transcription_annotation_page, entity_annotation_page = self._process_pagexml(pagexml_path)
            self.transcription_pages[page_id] = transcription_annotation_page
            if entity_annotation_page:
                self.entity_pages[page_id] = entity_annotation_page

    def _process_pagexml(self, pagexml_path: Path) -> tuple[
        str, dict[Any, Any] | dict[str, Any], dict[str, int] | None]:
        page_id = pagexml_path.name.split("/")[-1].replace(".xml", "")
        xmi_path = Path(f"{self.xmi_dir}/{page_id}.xmi")
        dp = DocumentPageProcessor(
            page_id=page_id,
            pagexml_path=pagexml_path,
            xmi_path=xmi_path,
            xpf=self.xmi_processor_factory,
            iiif_base_uri_idx=self.iiif_base_uri_idx,
            canvas_id_idx=self.canvas_id_idx,
            script_path=self.script_path
        )
        return page_id, dp.transcription_annotation_page, dp.entity_annotation_page

    def _load_manifest(self, manifest_path: str) -> None:
        logger.info(f"<= {manifest_path}")
        with open(manifest_path) as f:
            manifest = json.load(f)
        self.manifest_item_idx, self.iiif_base_uri_idx, self.canvas_id_idx = nx.index_manifest_items(manifest)


class DocumentPageProcessor:

    def __init__(self, page_id: str, pagexml_path: Path, xmi_path: Path, xpf: XMIProcessorFactory, iiif_base_uri_idx,
                 canvas_id_idx, script_path: str) -> None:
        self.page_id = page_id
        self.pagexml_path = pagexml_path
        self.xmi_path = xmi_path
        xml_string = self._read_page_xml(pagexml_path)
        self.transcription_annotation_page = {}
        self.entity_annotation_page = None

        normalized_page_text = ""
        canvas_id = uf.canvas_url(page_id)
        annotation_page_builder = pt.TranscriptionAnnotationPageBuilder(
            page_id=page_id,
            xml_string=xml_string,
            canvas_id=canvas_id,
            script_path=script_path,
            commit_id=xpf.commit_id
        )
        if xmi_path.exists():
            htr_word_offsets = annotation_page_builder.htr_word_offsets
            logger.info(f"<= {xmi_path}")
            # plain_text_source = nx.handle_page_xml(xmi_path.name, pagexml_path.name, xpf, iiif_base_uri_idx,
            #                                        canvas_id_idx)
            normalized_page_text = ""  # from xmi

            self.entity_annotation_page = {"x": 1}
        else:
            normalized_page_text = ""  # TODO: generate

        annotation_page_builder.normalized_page_text = normalized_page_text
        self.transcription_annotation_page = annotation_page_builder.build()

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
