#!/usr/bin/env python3
import csv
import json
from dataclasses import dataclass, field
from typing import Tuple, List

import hydra
from cassis import *
from dataclasses_json import dataclass_json
from icecream import ic
from loguru import logger
from omegaconf import DictConfig
from pagexml.model.physical_document_model import PageXMLTextRegion
from pagexml.parser import parse_pagexml_file
from pycaprio.core.mappings import InceptionFormat
from textrepo.client import TextRepoClient

from globalise_tools.inception_client import InceptionClient

typesystem_xml = 'data/typesystem.xml'
spacy_core = "nl_core_news_lg"


def is_paragraph(text_region: PageXMLTextRegion) -> bool:
    return text_region.type[-1] == "paragraph"


def output_path(page_xml_path: str) -> str:
    base = page_xml_path.split("/")[-1].replace(".xml", "")
    return f"out/{base}.xmi"


@logger.catch
def convert(page_xml_path: str):
    logger.info(f"<= {page_xml_path}")
    scan_doc = parse_pagexml_file(page_xml_path)

    text, paragraph_ranges = extract_paragraph_text(scan_doc)

    if not text:
        logger.warning(f"no paragraph text found in {page_xml_path}")
    else:
        logger.info(f"<= {typesystem_xml}")
        with open(typesystem_xml, 'rb') as f:
            typesystem = load_typesystem(f)

        cas = Cas(typesystem=typesystem)
        cas.sofa_string = text
        cas.sofa_mime = "text/plain"

        SentenceAnnotation = cas.typesystem.get_type("de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence")
        TokenAnnotation = cas.typesystem.get_type("de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token")
        ParagraphAnnotation = cas.typesystem.get_type("de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Paragraph")
        doc = nlp(text)
        for sentence in doc.sents:
            cas.add(SentenceAnnotation(begin=sentence.start_char, end=sentence.end_char))
            for token in [t for t in sentence if t.text != "\n"]:
                begin = token.idx
                end = token.idx + len(token.text)
                cas.add(TokenAnnotation(begin=begin, end=end))

        for pr in paragraph_ranges:
            cas.add(ParagraphAnnotation(begin=pr[0], end=pr[1]))

        # print_annotations(cas)

        cas_xmi = output_path(page_xml_path)
        logger.info(f"=> {cas_xmi}")
        cas.to_xmi(cas_xmi, pretty_print=True)


def paragraph_text(lines: List[str]) -> str:
    break_char = "„"
    # ic(lines)
    for i in range(0, len(lines) - 1):
        line0 = lines[i]
        line1 = lines[i + 1]
        if line0.endswith(break_char):
            lines[i] = line0.rstrip(break_char)
            lines[i + 1] = line1.lstrip(break_char)
        else:
            lines[i] = f"{line0} "
    # ic(lines)
    return "".join(lines) + "\n"


def extract_paragraph_text(scan_doc) -> Tuple[str, List[Tuple[int, int]]]:
    paragraph_ranges = []
    offset = 0
    text = ""
    for tr in scan_doc.get_text_regions_in_reading_order():
        if is_paragraph(tr):
            lines = []
            for line in tr.lines:
                if line.text:
                    lines.append(line.text)
            text += paragraph_text(lines)
            text_len = len(text)
            paragraph_ranges.append((offset, text_len))
            offset = text_len
    return text, paragraph_ranges


def print_annotations(cas):
    for a in cas.views[0].get_all_annotations():
        print(a)
        print(f"'{a.get_covered_text()}'")
        print()


def join_words(px_words):
    text = ""
    last_text_region = None
    last_line = None
    for w in px_words:
        if w.text_region_id == last_text_region:
            if w.line_id != last_line:
                text += "|\n"
            text += " "
        else:
            text += "\n\n"
        text += w.text
        last_text_region = w.text_region_id
        last_line = w.line_id
    return text.strip()


@logger.catch
def import_document(document_id: str, first_page: int, last_page: int, base_uri: str, api_key: str):
    ic(document_id, first_page, last_page)
    trc = TextRepoClient(base_uri, api_key=api_key, verbose=False)
    for p in range(first_page, last_page):
        external_id = f"{document_id}_{p:04d}"
        pagexml = trc.find_latest_file_contents(external_id, "pagexml")
        out_file = f"out/{external_id}.xml"
        logger.info(f"=> {out_file}")
        with open(out_file, "wb") as f:
            f.write(pagexml)
        meta = trc.find_document_metadata(external_id)[1]
        scan_url = meta['scan_url']
        iiif_url = f"{scan_url}/full/max/0/default.jpg"
        print(f"{external_id} :")
        print(f"\t{iiif_url}")
        print()


@dataclass_json
@dataclass
class DocumentMetadata:
    document_id: str
    title: str
    year_creation_or_dispatch: str
    inventory_number: str
    folio_or_page: str
    folio_or_page_range: str
    scan_range: str
    scan_start: str
    scan_end: str
    no_of_scans: int
    no_of_pages: int
    GM_id: str
    remarks: str
    first_scan_nr: int = field(init=False)
    last_scan_nr: int = field(init=False)
    hana_nr: str = field(init=False)
    external_id: str = field(init=False)
    pagexml_ids: List[str] = field(init=False)

    def __post_init__(self):
        self.no_of_pages = int(self.no_of_pages)
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
        return [f"{self.hana_nr}_{n:04d}" for n in range(self.first_scan_nr, self.last_scan_nr)]


def generate_xmi(pagexml_ids: List[str]) -> str:
    return "just a test"


def store_results():
    path = "out/results.json"
    logger.info(f"=> {path}")
    with open(path, 'w') as f:
        json.dump(results, fp=f)


@hydra.main(version_base=None)
@logger.catch
def main(cfg: DictConfig) -> None:
    metadata = read_document_selection(cfg)
    trc = TextRepoClient(cfg.textrepo.base_uri, api_key=cfg.textrepo.api_key, verbose=False)
    file_type = get_xmi_file_type(trc)
    inc, project_id = init_inception_client(cfg)
    results['textrepo_links'] = {}
    for dm in metadata:
        links = {}
        document_identifier = create_tr_document(dm, trc)
        links['tr_document'] = f"{trc.base_uri}/rest/documents/{document_identifier.id}"
        links['tr_metadata'] = f"{trc.base_uri}/rest/documents/{document_identifier.id}/metadata"
        xmi = generate_xmi(dm.pagexml_ids)
        file_locator = trc.create_document_file(document_identifier, type_id=file_type.id)
        links['tr_file'] = f"{trc.base_uri}/rest/files/{file_locator.id}"
        version_identifier = trc.create_version(file_locator.id, xmi)
        links['tr_version'] = f"{trc.base_uri}/rest/versions/{version_identifier.id}"
        name = f'{dm.external_id} - {dm.title}'
        response = inc.create_project_document(project_id=project_id, data=xmi, name=name,
                                               format=InceptionFormat.TEXT)
        idoc_id = response.body['id']
        links['inception_view'] = f"{inc.base_uri}/p/{cfg.inception.project_name}/annotate#!d={idoc_id}"
        # format = InceptionFormat.UIMA_CAS_XMI_XML_1_1)
        results['textrepo_links'][dm.external_id] = links
    store_results()


def read_document_selection(cfg):
    logger.info(f"<= {cfg.selection_file}")
    with open(cfg.selection_file) as f:
        reader = csv.DictReader(f)
        metadata = [DocumentMetadata.from_dict(row) for row in reader]
    return metadata


def init_inception_client(cfg) -> (InceptionClient, int):
    inception_cfg = cfg.inception
    authorization = inception_cfg.get('authorization', None)
    base = cfg.inception.base_uri
    if authorization:
        client = InceptionClient(base_uri=base, authorization=authorization, cookie=cfg.inception.cookie)
    else:
        client = InceptionClient(base_uri=base, user=cfg.inception.user, password=cfg.inception.password)
    result = client.create_project(name=cfg.inception.project_name)
    ic(result)
    return client, result.body['id']


def get_xmi_file_type(client: TextRepoClient):
    file_type_name = 'xmi'
    if client.has_file_type_with_name(file_type_name):
        file_type = client.find_file_type(file_type_name)
    else:
        file_type = client.create_file_type('xmi', 'application/vnd.xmi+xml')
    return file_type


def create_tr_document(metadata: DocumentMetadata, client: TextRepoClient):
    try:
        client.purge_document(external_id=metadata.external_id)
    except:
        pass
    document_identifier = client.create_document(external_id=metadata.external_id)
    document_id = document_identifier.id
    client.set_document_metadata(document_id=document_id, key='title', value=metadata.title)
    client.set_document_metadata(document_id=document_id, key='year_creation_or_dispatch',
                                 value=metadata.year_creation_or_dispatch)
    client.set_document_metadata(document_id=document_id, key='inventory_number',
                                 value=metadata.inventory_number)
    client.set_document_metadata(document_id=document_id, key='folio_or_page', value=metadata.folio_or_page)
    client.set_document_metadata(document_id=document_id, key='folio_or_page_range',
                                 value=metadata.folio_or_page_range)
    client.set_document_metadata(document_id=document_id, key='scan_range', value=metadata.scan_range)
    client.set_document_metadata(document_id=document_id, key='scan_start', value=metadata.scan_start)
    client.set_document_metadata(document_id=document_id, key='scan_end', value=metadata.scan_end)
    client.set_document_metadata(document_id=document_id, key='no_of_scans', value=str(metadata.no_of_scans))
    client.set_document_metadata(document_id=document_id, key='no_of_pages', value=str(metadata.no_of_pages))
    client.set_document_metadata(document_id=document_id, key='GM_id', value=metadata.GM_id)
    client.set_document_metadata(document_id=document_id, key='remarks', value=metadata.remarks)
    return document_identifier


results = {}

if __name__ == '__main__':
    main()
