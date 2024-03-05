#!/usr/bin/env python3
import csv
import dataclasses
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Tuple, List, Dict, Any

import hydra
import spacy
from cassis import *
from cassis.typesystem import TYPE_NAME_STRING
from dataclasses_json import dataclass_json
from loguru import logger
from omegaconf import DictConfig
from pagexml.model.physical_document_model import PageXMLScan
from pagexml.parser import parse_pagexml_file
from provenance.client import ProvenanceClient, ProvenanceData, ProvenanceHow, ProvenanceWhy, ProvenanceResource
from pycaprio.core.mappings import InceptionFormat
from spacy import Language
from textrepo.client import TextRepoClient
from uri import URI

from globalise_tools.inception_client import InceptionClient
from globalise_tools.model import CAS_SENTENCE, CAS_TOKEN, CAS_PARAGRAPH, CAS_MARGINALIUM, CAS_HEADER
from globalise_tools.tools import is_paragraph, is_marginalia, paragraph_text, is_header, is_signature

typesystem_xml = 'data/typesystem.xml'
spacy_core = "nl_core_news_lg"


@dataclass_json
@dataclass
class DocumentMetadata:
    document_id: str
    internal_id: str
    quality_check: str
    title: str
    year_creation_or_dispatch: str
    inventory_number: str
    folio_or_page: str
    folio_or_page_range: str
    scan_range: str
    scan_start: str
    scan_end: str
    no_of_scans: str
    no_of_pages: str
    GM_id: str
    tanap_id: str
    tanap_description: str
    remarks: str
    marginalia: str
    partOf500_filename: str
    partOf500_folio: str
    first_scan_nr: int = field(init=False)
    last_scan_nr: int = field(init=False)
    hana_nr: str = field(init=False)
    external_id: str = field(init=False)
    pagexml_ids: List[str] = field(init=False)

    def __post_init__(self):
        if self.no_of_pages:
            self.no_of_pages = int(self.no_of_pages)
        else:
            self.no_of_pages = 1
        if self.no_of_scans:
            self.no_of_scans = int(self.no_of_scans)
        else:
            self.no_of_scans = 1
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


@hydra.main(version_base=None)
@logger.catch
def main(cfg: DictConfig) -> None:
    results = {}
    document_id_idx = {}
    metadata = read_document_selection(cfg)

    logger.info(f"loading {spacy_core}")
    nlp: Language = spacy.load(spacy_core)

    script_args = " ".join(sys.argv[1:])
    commit_id = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
    base_provenance = ProvenanceData(
        who=URI(cfg.provenance.who),
        where=URI(cfg.provenance.where),
        when=datetime.now(),
        how=ProvenanceHow(
            software=URI(
                f'https://raw.githubusercontent.com/knaw-huc/globalise-tools/{commit_id}/'
                f'scripts/gt-import-document.py'),
            init=script_args
        ),
        why=ProvenanceWhy(motivation="converting"),
        sources=[],
        targets=[],
    )

    textrepo_client = TextRepoClient(cfg.textrepo.base_uri, api_key=cfg.textrepo.api_key, verbose=False)
    inception_client, project_id = init_inception_client(cfg)
    provenance_client = ProvenanceClient(base_url=cfg.provenance.base_uri, api_key=cfg.provenance.api_key)
    quality_checked_metadata = [m for m in metadata if m.quality_check == 'TRUE']
    with textrepo_client as trc, inception_client as inc, provenance_client as prc:
        file_type = get_xmi_file_type(trc)
        for dm in quality_checked_metadata:
            inventory_id = dm.inventory_number
            Path(f"out/{inventory_id}").mkdir(parents=True, exist_ok=True)
            links = {'textrepo_links': {}}
            document_identifier = create_or_update_tr_document(dm, trc)
            links['textrepo_links']['document'] = f"{trc.base_uri}/rest/documents/{document_identifier.id}"
            links['textrepo_links']['metadata'] = f"{trc.base_uri}/rest/documents/{document_identifier.id}/metadata"
            xmi_path, xmi_provenance = generate_xmi(
                textrepo_client=trc,
                document_id=dm.external_id,
                inventory_id=inventory_id,
                nlp=nlp,
                pagexml_ids=dm.pagexml_ids,
                links=links,
                base_provenance=base_provenance
            )
            with open(xmi_path) as file:
                contents = file.read()
            version_identifier = trc.import_version(
                external_id=dm.external_id,
                type_name=file_type.name,
                contents=contents,
                as_latest_version=True
            )
            links['textrepo_links']['file'] = f"{trc.base_uri}/rest/files/{version_identifier.file_id}"
            version_uri = f"{trc.base_uri}/rest/versions/{version_identifier.version_id}"
            xmi_provenance.targets.append(ProvenanceResource(resource=URI(version_uri), relation="primary"))

            links['textrepo_links']['version'] = version_uri
            file_name = f'{dm.external_id}.xmi'
            trc.set_file_metadata(file_id=version_identifier.file_id, key='file_name', value=file_name)
            document_id_idx[dm.external_id] = version_identifier.document_id

            response = inc.create_project_document(
                project_id=project_id,
                file_path=xmi_path,
                name=inception_document_name(dm),
                file_format=InceptionFormat.UIMA_CAS_XMI_XML_1_1
            )
            idoc_id = response.body['id']
            inception_view = f"{inc.base_uri}/p/{cfg.inception.project_name}/annotate#!d={idoc_id}"
            links['inception_view'] = inception_view

            provenance = dataclasses.replace(
                base_provenance,
                sources=[ProvenanceResource(resource=URI(version_uri), relation='primary')],
                targets=[ProvenanceResource(resource=URI(inception_view), relation='primary')],
            )
            xmi_provenance_id = prc.add_provenance(xmi_provenance)
            provenance_id = prc.add_provenance(provenance)
            links['provenance_links'] = [str(xmi_provenance_id.location), str(provenance_id.location)]
            results[dm.external_id] = links
    results['document_id_idx'] = document_id_idx
    store_results(results)


def inception_document_name(dm):
    if dm.year_creation_or_dispatch:
        year = dm.year_creation_or_dispatch
    else:
        year = "<year unknown>"
    if dm.title:
        title = cut_off(dm.title, 100)
    else:
        title = "<no title>"
    name = f'{dm.external_id} - {year} - {title}'
    return name


def extract_paragraph_text(scan_doc) -> Tuple[str, List[Tuple[int, int]], Tuple[int, int], List[Tuple[int, int]]]:
    headers, marginalia, paragraphs = extract_text(scan_doc)

    marginalia_ranges = []
    header_range = None
    paragraph_ranges = []
    offset = 0
    text = ""
    for m in marginalia:
        text += m
        text_len = len(text)
        marginalia_ranges.append((offset, text_len))
        offset = text_len
    if headers:
        h = headers[0]
        text += f"\n{h}\n"
        text_len = len(text)
        header_range = (offset + 1, text_len - 1)
        offset = text_len
    for m in paragraphs:
        text += m
        text_len = len(text)
        paragraph_ranges.append((offset, text_len))
        offset = text_len
    if '  ' in text:
        logger.error('double space in text')
    return text, marginalia_ranges, header_range, paragraph_ranges


_RE_COMBINE_WHITESPACE = re.compile(r"\s+")


def joined_lines(tr):
    lines = []
    for line in tr.lines:
        if line.text:
            lines.append(line.text)
    ptext = paragraph_text(lines)
    return _RE_COMBINE_WHITESPACE.sub(" ", ptext)


def store_document_text(inventory_id, document_id, marginalia, headers, paragraphs):
    document_text = "# marginalia\n"
    document_text += "\n".join(marginalia)
    document_text += "\n\n# header\n"
    if headers:
        document_text += headers[0]
    document_text += "\n\n# paragraphs\n"
    document_text += "\n".join(paragraphs)

    path = f"out/{inventory_id}/{document_id}.txt"
    logger.info(f"=> {path}")
    with open(path, 'w') as f:
        f.write(document_text)


def generate_xmi(
        textrepo_client: TextRepoClient,
        document_id: str,
        inventory_id: str,
        nlp: Language,
        pagexml_ids: List[str],
        base_provenance: ProvenanceData,
        links: Dict[str, Any]
) -> Tuple[str, ProvenanceData]:
    provenance = dataclasses.replace(base_provenance, sources=[], targets=[])

    logger.info(f"<= {typesystem_xml}")
    with open(typesystem_xml, 'rb') as f:
        typesystem = load_typesystem(f)

    cas = Cas(typesystem=typesystem)
    cas.sofa_string = ""
    cas.sofa_mime = "text/plain"

    MarginaliaAnnotation = typesystem.create_type("pagexml.Marginalia")
    typesystem.create_feature(domainType=MarginaliaAnnotation, name="url", rangeType=TYPE_NAME_STRING)

    ParagraphAnnotation = typesystem.create_type("webanno.custom.Paragraph")
    typesystem.create_feature(domainType=ParagraphAnnotation, name="type", rangeType=TYPE_NAME_STRING)
    typesystem.create_feature(domainType=ParagraphAnnotation, name="iiif_url", rangeType=TYPE_NAME_STRING)

    SentenceAnnotation = cas.typesystem.get_type(CAS_SENTENCE)
    TokenAnnotation = cas.typesystem.get_type(CAS_TOKEN)
    ParagraphAnnotation = cas.typesystem.get_type(CAS_PARAGRAPH)
    MarginaliumAnnotation = cas.typesystem.get_type(CAS_MARGINALIUM)
    HeaderAnnotation = cas.typesystem.get_type(CAS_HEADER)

    typesystem_path = "out/typesystem.xml"
    logger.info(f"=> {typesystem_path}")
    typesystem.to_xml(typesystem_path)

    scan_links = {}

    document_marginalia = []
    document_headers = []
    document_paragraphs = []

    for external_id in pagexml_ids:
        page_links = {}
        page_xml_path = download_page_xml(inventory_id, external_id, textrepo_client)
        version_identifier = textrepo_client.find_latest_version(external_id, "pagexml")
        version_location = textrepo_client.version_uri(version_identifier.id)
        provenance.sources.append(ProvenanceResource(resource=URI(version_location), relation="primary"))

        iiif_url = get_iiif_url(external_id, textrepo_client)
        logger.info(f"iiif_url={iiif_url}")
        page_links['iiif_url'] = iiif_url
        logger.info(f"<= {page_xml_path}")
        scan_doc: PageXMLScan = parse_pagexml_file(page_xml_path)
        page_marginalia, page_headers, page_paragraphs = extract_text(scan_doc)
        document_marginalia.extend(page_marginalia)
        document_headers.extend(page_headers)
        document_paragraphs.extend(page_paragraphs)
        scan_links[external_id] = page_links

    store_document_text(inventory_id, document_id, document_marginalia, document_headers, document_paragraphs)
    marginalia_ranges = []
    header_range = None
    paragraph_ranges = []
    offset = 0
    document_text = ""
    for m in document_marginalia:
        document_text += m
        text_len = len(document_text)
        marginalia_ranges.append((offset, text_len))
        offset = text_len
    if document_headers:
        h = document_headers[0]
        document_text += f"\n{h}\n"
        text_len = len(document_text)
        header_range = (offset + 1, text_len - 1)
        offset = text_len
    for m in document_paragraphs:
        document_text += m
        text_len = len(document_text)
        paragraph_ranges.append((offset, text_len))
        offset = text_len
    if '  ' in document_text:
        logger.error('double space in text')

    cas.sofa_string = document_text
    doc = nlp(document_text)
    for sentence in doc.sents:
        for token in [t for t in sentence if t.text != "\n"]:
            begin = token.idx
            end = begin + len(token.text)
            cas.add(TokenAnnotation(begin=begin, end=end))

    ranges = marginalia_ranges
    if header_range:
        ranges.append(header_range)
    ranges.extend(paragraph_ranges)
    for r in ranges:
        cas.add(SentenceAnnotation(begin=r[0], end=r[1]))

    links['scan_links'] = scan_links

    xmi_path = f"out/{inventory_id}/{document_id}.xmi"
    logger.info(f"=> {xmi_path}")
    cas.to_xmi(xmi_path, pretty_print=True)

    return xmi_path, provenance


def extract_text(scan_doc) -> (List[str], List[str], List[str]):
    paragraphs = []
    headers = []
    marginalia = []
    for tr in scan_doc.get_text_regions_in_reading_order():
        logger.info(f"text_region: {tr.id}")
        logger.info(f"type: {tr.type[-1]}")
        line_text = [l.text for l in tr.lines]
        for t in line_text:
            logger.info(f"line: {t}")
        if is_marginalia(tr):
            ptext = joined_lines(tr)
            if ptext:
                marginalia.append(ptext)
        if is_header(tr):
            ptext = joined_lines(tr)
            if ptext:
                headers.append(ptext)
        if is_paragraph(tr) or is_signature(tr):
            ptext = joined_lines(tr)
            if ptext:
                paragraphs.append(ptext)
        logger.info("")
    return marginalia, headers, paragraphs


def get_iiif_url(external_id, textrepo_client):
    meta = textrepo_client.find_document_metadata(external_id)[1]
    scan_url = meta['scan_url']
    return f"{scan_url}/full/max/0/default.jpg"


def download_page_xml(inventory_id, external_id, textrepo_client):
    pagexml = textrepo_client.find_latest_file_contents(external_id, "pagexml").decode('utf8')
    page_xml_path = f"out/{inventory_id}/{external_id}.xml"
    logger.info(f"=> {page_xml_path}")
    with open(page_xml_path, "w") as f:
        f.write(pagexml)
    return page_xml_path


def store_results(results):
    path = "out/results.json"
    logger.info(f"=> {path}")
    with open(path, 'w') as f:
        json.dump(results, fp=f)


def cut_off(string: str, max_len: int) -> str:
    max_len = max(max_len, 3)
    l = len(string)
    if l <= max_len:
        return string
    else:
        return f"{string[:(max_len - 3)]}..."


def read_document_selection(cfg) -> List[DocumentMetadata]:
    logger.info(f"<= {cfg.selection_file}")
    with open(cfg.selection_file, encoding='utf8') as f:
        f.readline()
        reader = csv.DictReader(f, fieldnames=[
            "document_id", "internal_id", "quality_check", "title", "year_creation_or_dispatch", "inventory_number",
            "folio_or_page", "folio_or_page_range", "scan_range", "scan_start", "scan_end", "no_of_scans",
            "no_of_pages", "GM_id", "tanap_id", "tanap_description", "remarks", "marginalia",
            "partOf500_filename", "partOf500_folio"])
        all_metadata = [DocumentMetadata.from_dict(row) for row in reader]
    # return [m for m in all_metadata if m.quality_check == 'TRUE']
    return all_metadata


def init_inception_client(cfg) -> (InceptionClient, int):
    inception_cfg = cfg.inception
    authorization = inception_cfg.get('authorization', None)
    base = cfg.inception.base_uri
    if authorization:
        client = InceptionClient(base_uri=base, authorization=authorization, oauth2_proxy=cfg.inception.oauth2_proxy)
    else:
        client = InceptionClient(base_uri=base, user=cfg.inception.user, password=cfg.inception.password)
    project = client.get_project_by_name(name=cfg.inception.project_name)
    if not project:
        result = client.create_project(name=cfg.inception.project_name)
        project_id = result.body['id']
    else:
        project_id = project.id
    return client, project_id


def get_xmi_file_type(client: TextRepoClient):
    file_type_name = 'xmi'
    if client.has_file_type_with_name(file_type_name):
        file_type = client.find_file_type(file_type_name)
    else:
        file_type = client.create_file_type('xmi', 'application/vnd.xmi+xml')
    return file_type


def create_or_update_tr_document(metadata: DocumentMetadata, client: TextRepoClient):
    document_identifier = client.read_document_by_external_id(metadata.external_id)
    if not document_identifier:
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
    client.set_document_metadata(document_id=document_id, key='tanap_id', value=metadata.tanap_id)
    client.set_document_metadata(document_id=document_id, key='tanap_description', value=metadata.tanap_description)
    client.set_document_metadata(document_id=document_id, key='remarks', value=metadata.remarks)
    client.set_document_metadata(document_id=document_id, key='marginalia', value=metadata.marginalia)
    client.set_document_metadata(document_id=document_id, key='partOf500_filename', value=metadata.partOf500_filename)
    client.set_document_metadata(document_id=document_id, key='partOf500_folio', value=metadata.partOf500_folio)
    return document_identifier


if __name__ == '__main__':
    main()
