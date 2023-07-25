#!/usr/bin/env python3
import csv
import dataclasses
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Tuple, List, Dict, Any

import hydra
import spacy
from cassis import *
from cassis.typesystem import TYPE_NAME_STRING
from dataclasses_json import dataclass_json
from loguru import logger
from omegaconf import DictConfig
from pagexml.model.physical_document_model import PageXMLTextRegion, PageXMLScan, Coords
from pagexml.parser import parse_pagexml_file
from provenance.client import ProvenanceClient, ProvenanceData, ProvenanceHow, ProvenanceWhy, ProvenanceResource
from pycaprio.core.mappings import InceptionFormat
from spacy import Language
from textrepo.client import TextRepoClient
from uri import URI

from globalise_tools.inception_client import InceptionClient

typesystem_xml = 'data/typesystem.xml'
spacy_core = "nl_core_news_lg"


@dataclass_json
@dataclass
class DocumentMetadata:
    document_id: str
    internal_id: str
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
    with textrepo_client as trc, inception_client as inc, provenance_client as prc:
        file_type = get_xmi_file_type(trc)
        for dm in metadata:
            links = {'textrepo_links': {}}
            document_identifier = create_or_update_tr_document(dm, trc)
            links['textrepo_links']['document'] = f"{trc.base_uri}/rest/documents/{document_identifier.id}"
            links['textrepo_links']['metadata'] = f"{trc.base_uri}/rest/documents/{document_identifier.id}/metadata"
            xmi_path, xmi_provenance = generate_xmi(
                textrepo_client=trc,
                document_id=dm.external_id,
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
            document_id_idx[dm.external_id] = version_identifier.version_id

            name = f'{dm.external_id} - {dm.year_creation_or_dispatch} - {cut_off(dm.title, 100)}'
            response = inc.create_project_document(project_id=project_id, file_path=xmi_path, name=name,
                                                   file_format=InceptionFormat.UIMA_CAS_XMI_XML_1_1)
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


def is_paragraph(text_region: PageXMLTextRegion) -> bool:
    return text_region.type[-1] == "paragraph"


def is_magrginalium(text_region: PageXMLTextRegion) -> bool:
    return text_region.type[-1] == "marginalia"


def joined_text(lines: List[str]) -> str:
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


def extract_paragraph_text(scan_doc: PageXMLScan, start_offset: int) -> Tuple[str, List[Tuple[int, int]], List[Coords]]:
    paragraph_ranges = []
    paragraph_coords = []
    text = ""
    offset = start_offset
    for tr in scan_doc.get_text_regions_in_reading_order():
        if is_paragraph(tr) or is_magrginalium(tr):
            lines = []
            for line in tr.lines:
                if line.text:
                    lines.append(line.text)
            text += joined_text(lines)
            text_len = len(text)
            paragraph_ranges.append((offset, start_offset + text_len))
            offset = start_offset + text_len
            paragraph_coords.append(tr.coords)
    return text, paragraph_ranges, paragraph_coords


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


def generate_xmi(
        textrepo_client: TextRepoClient,
        document_id: str,
        nlp: Language,
        pagexml_ids: List[str],
        base_provenance: ProvenanceData,
        links: Dict[str, Any]
) -> Tuple[str, ProvenanceData]:
    logger.info(f"<= {typesystem_xml}")
    provenance = dataclasses.replace(base_provenance, sources=[], targets=[])

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

    SentenceAnnotation = cas.typesystem.get_type("de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence")
    TokenAnnotation = cas.typesystem.get_type("de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token")
    # ParagraphAnnotation = cas.typesystem.get_type(
    #     "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Paragraph")
    typesystem_path = "out/typesystem.xml"
    logger.info(f"=> {typesystem_path}")
    typesystem.to_xml(typesystem_path)

    scan_links = {}

    for external_id in pagexml_ids:
        page_links = {}
        page_xml_path = download_page_xml(external_id, textrepo_client)
        version_identifier = textrepo_client.find_latest_version(external_id, "pagexml")
        version_location = textrepo_client.version_uri(version_identifier.id)
        provenance.sources.append(ProvenanceResource(resource=URI(version_location), relation="primary"))

        iiif_url = get_iiif_url(external_id, textrepo_client)
        logger.info(f"iiif_url={iiif_url}")
        page_links['iiif_url'] = iiif_url
        page_links['paragraph_iiif_urls'] = []
        page_links['sentences'] = []
        logger.info(f"<= {page_xml_path}")
        scan_doc: PageXMLScan = parse_pagexml_file(page_xml_path)
        start_offset = len(cas.sofa_string)
        paragraph_text, paragraph_ranges, paragraph_coords = extract_paragraph_text(
            scan_doc=scan_doc,
            start_offset=start_offset
        )

        if not paragraph_text:
            logger.warning(f"no paragraph text found in {page_xml_path}")
        else:
            cas.sofa_string += paragraph_text
            doc = nlp(paragraph_text)
            for sentence in doc.sents:
                page_links['sentences'].append(sentence.text_with_ws)
                sentence_start_char = start_offset + sentence.start_char
                sentence_end_char = start_offset + sentence.end_char
                # cas.add(
                #     SentenceAnnotation(begin=sentence_start_char, end=sentence_end_char))
                for token in [t for t in sentence if t.text != "\n"]:
                    begin = start_offset + token.idx
                    end = begin + len(token.text)
                    cas.add(TokenAnnotation(begin=begin, end=end))

            for pr, coords in zip(paragraph_ranges, paragraph_coords):
                xywh = ",".join([str(coords.x), str(coords.y), str(coords.w), str(coords.h)])
                paragraph_iiif_url = iiif_url.replace("full", xywh)
                cas.add(SentenceAnnotation(begin=pr[0], end=pr[1]))
                cas.add(ParagraphAnnotation(begin=pr[0], end=pr[1], type_='paragraph', iiif_url=iiif_url))
                page_links['paragraph_iiif_urls'].append(paragraph_iiif_url)

        scan_links[external_id] = page_links

    links['scan_links'] = scan_links

    xmi_path = f"out/{document_id}.xmi"
    logger.info(f"=> {xmi_path}")
    cas.to_xmi(xmi_path, pretty_print=True)

    return xmi_path, provenance


def get_iiif_url(external_id, textrepo_client):
    meta = textrepo_client.find_document_metadata(external_id)[1]
    scan_url = meta['scan_url']
    return f"{scan_url}/full/max/0/default.jpg"


def download_page_xml(external_id, textrepo_client):
    pagexml = textrepo_client.find_latest_file_contents(external_id, "pagexml").decode('utf8')
    page_xml_path = f"out/{external_id}.xml"
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


def store_xmi(dm, xmi):
    xmi_path = f"out/{dm.external_id}.xmi"
    logger.info(f"=> {xmi_path}")
    with open(xmi_path, 'w') as f:
        f.write(xmi)


def read_document_selection(cfg) -> List[DocumentMetadata]:
    logger.info(f"<= {cfg.selection_file}")
    with open(cfg.selection_file, encoding='utf8') as f:
        reader = csv.DictReader(f)
        metadata = [DocumentMetadata.from_dict(row) for row in reader]
    return metadata


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
    client.set_document_metadata(document_id=document_id, key='remarks', value=metadata.remarks)
    return document_identifier


if __name__ == '__main__':
    main()
