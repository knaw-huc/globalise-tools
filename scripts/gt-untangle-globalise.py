#!/usr/bin/env python3
import csv
import dataclasses
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

import hydra
from dataclasses_json import dataclass_json
from icecream import ic
from loguru import logger
from omegaconf import DictConfig
from pagexml.model.physical_document_model import PageXMLTextRegion, PageXMLScan, Coords
from pagexml.parser import parse_pagexml_file
from provenance.client import ProvenanceClient, ProvenanceData, ProvenanceHow, ProvenanceWhy, ProvenanceResource
from textrepo.client import TextRepoClient
from uri import URI

import globalise_tools.tools as gt
from globalise_tools.model import AnnotationEncoder, WebAnnotation
from globalise_tools.tools import WebAnnotationFactory, Annotation


@dataclass
class SimpleAnnotation:
    type: str
    first_anchor: int
    last_anchor: int
    text: str
    coords: Optional[Coords]
    metadata: dict[str, Any] = field(default_factory=dict, hash=False)


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
    nl_hana_nr: str = field(init=False)
    external_id: str = field(init=False)
    pagexml_ids: List[str] = field(init=False)

    def __post_init__(self):
        # self.no_of_pages = int(self.no_of_pages)
        self.no_of_scans = int(self.no_of_scans)
        (self.first_scan_nr, self.last_scan_nr) = self._scan_nr_range()
        self.nl_hana_nr = f"NL-HaNA_1.04.02_{self.inventory_number}"
        self.external_id = self._external_id()
        self.pagexml_ids = self._pagexml_ids()

    def _scan_nr_range(self) -> (int, int):
        (first_str, last_str) = self.scan_range.split('-')
        first = int(first_str)
        last = int(last_str)
        return first, last

    def _external_id(self) -> str:
        return f"{self.nl_hana_nr}_{self.first_scan_nr:04d}-{self.last_scan_nr:04d}"

    def _pagexml_ids(self) -> List[str]:
        return [f"{self.nl_hana_nr}_{n:04d}" for n in range(self.first_scan_nr, self.last_scan_nr + 1)]


@hydra.main(version_base=None)
@logger.catch
def main(cfg: DictConfig) -> None:
    results = {}
    metadata = read_na_file_metadata(cfg.documents_file)
    base_provenance = generate_base_provenance(cfg)
    textrepo_client = TextRepoClient(cfg.textrepo.base_uri, api_key=cfg.textrepo.api_key, verbose=False)
    provenance_client = ProvenanceClient(base_url=cfg.provenance.base_uri, api_key=cfg.provenance.api_key)
    dm_selection = sorted(metadata, key=lambda x: x.no_of_scans)[:10]
    # dm_selection = metadata
    webannotation_factory = WebAnnotationFactory(cfg.iiif_mapping_file)

    with textrepo_client as trc, provenance_client as prc:
        for dm in dm_selection:
            # ic(dm)
            process_na_file(base_provenance, dm, prc, trc, webannotation_factory, results)


def process_na_file(base_provenance: ProvenanceData, document_metadata: DocumentMetadata, prov_client: ProvenanceClient,
                    tr_client: TextRepoClient, waf: WebAnnotationFactory, results: Dict[str, any]):
    links = {'textrepo_links': {}, 'errors': []}

    document_identifier = create_or_update_tr_document(document_metadata, tr_client)

    links['textrepo_links']['document'] = f"{tr_client.base_uri}/rest/documents/{document_identifier.id}"
    links['textrepo_links']['metadata'] = f"{tr_client.base_uri}/rest/documents/{document_identifier.id}/metadata"

    segmented_text, text_provenance, annotations = untangle_na_file(
        document_id=document_metadata.nl_hana_nr,
        textrepo_client=tr_client,
        pagexml_ids=document_metadata.pagexml_ids,
        links=links,
        base_provenance=base_provenance
    )
    version_identifier = tr_client.import_version(
        external_id=document_metadata.external_id,
        type_name='segmented_text',
        contents=json.dumps(segmented_text, ensure_ascii=False),
        as_latest_version=True
    )
    links['textrepo_links']['file'] = f"{tr_client.base_uri}/rest/files/{version_identifier.file_id}"

    version_uri = f"{tr_client.base_uri}/rest/versions/{version_identifier.version_id}"
    links['textrepo_links']['version'] = version_uri

    text_provenance.targets.append(ProvenanceResource(resource=URI(version_uri), relation="primary"))

    links['textrepo_links']['contents'] = (f"{tr_client.base_uri}/task/find/{document_metadata.external_id}"
                                           f"/file/contents?type=segmented_text")

    file_name = f'{document_metadata.nl_hana_nr}.json'
    tr_client.set_file_metadata(file_id=version_identifier.file_id, key='file_name', value=file_name)
    # provenance = dataclasses.replace(
    #     base_provenance,
    #     sources=[ProvenanceResource(resource=URI(version_uri), relation='primary')],
    #     targets=[ProvenanceResource(resource=URI(inception_view), relation='primary')],
    # )
    text_provenance_id = prov_client.add_provenance(text_provenance)
    # provenance_id = prc.add_provenance(provenance)
    prov_json_link = str(text_provenance_id.location)
    prov_html_link = prov_json_link.replace('prov/', '#')
    links['provenance_links'] = [prov_json_link, prov_html_link]
    results[document_metadata.external_id] = links

    # annotations = add_tr_view(annotations=annotations,
    #                           textrepo_base_url=tr_client.base_uri,
    #                           segmented_version_id=version_identifier.version_id)
    # links['annotations'] = [a.__dict__ for a in annotations]

    store_results(results)

    for a in annotations:
        a.segmented_version_id = version_identifier.version_id
        a.begin_anchor = a.offset
        a.end_anchor = a.offset + a.length - 1

    web_annotations = [to_web_annotation(a, webannotation_factory=waf) for a in annotations]
    web_annotations.insert(
        0,
        document_web_annotation(annotations, document_metadata.nl_hana_nr, waf, version_identifier.version_id)
    )

    export_web_annotations(document_metadata, web_annotations)


def to_web_annotation(annotation: Annotation,
                      webannotation_factory: WebAnnotationFactory) -> WebAnnotation:
    body_id = annotation.id
    body = {
        "id": body_id,
        "type": annotation.type,
        "metadata": annotation.metadata
    }
    targets = webannotation_factory.annotation_targets(annotation)
    body['metadata'].pop("coords", None)
    return WebAnnotation(body=body, target=targets)


def document_web_annotation(all_annotations: List[Annotation], document_id: str,
                            webannotation_factory: WebAnnotationFactory, segmented_version_id: str) -> WebAnnotation:
    manifest_id = document_id
    manifest_url = f"https://broccoli.tt.di.huc.knaw.nl/mock/globalise/manifest-{manifest_id}.json"
    textrepo_base_url = "https://globalise.tt.di.huc.knaw.nl/textrepo"
    end_anchor = max([a.end_anchor for a in all_annotations])
    return (WebAnnotation(
        body={
            "@context": {"na": "https://brambg.github.io/ns/nationaal-archief#"},
            "id": f"urn:globalise:{document_id}:file",
            "type": "na:File",
            "metadata": {
                "file": document_id,
                "manifest": manifest_url
            }
        },
        target=[webannotation_factory.text_anchor_selector_target(textrepo_base_url=textrepo_base_url,
                                                                  segmented_version_id=segmented_version_id,
                                                                  begin_anchor=0, end_anchor=end_anchor),
                gt.cutout_target(textrepo_base_url=textrepo_base_url, segmented_version_id=segmented_version_id,
                                 begin_anchor=0, end_anchor=end_anchor)]
    ))


def export_web_annotations(document_metadata, web_annotations):
    path = f"out/{document_metadata.nl_hana_nr}/web_annotations.json"
    logger.debug(f"=>{path}")
    with open(path, "w") as f:
        json.dump(web_annotations, fp=f, indent=4, ensure_ascii=False, cls=AnnotationEncoder)


def generate_base_provenance(cfg) -> ProvenanceData:
    script_args = " ".join(sys.argv[1:])
    commit_id = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
    base_provenance = ProvenanceData(
        who=URI(cfg.provenance.who),
        where=URI(cfg.provenance.where),
        when=datetime.now(),
        how=ProvenanceHow(
            software=URI(
                f'https://raw.githubusercontent.com/knaw-huc/globalise-tools/{commit_id}/'
                f'scripts/gt-untangle-globalise.py'),
            init=script_args
        ),
        why=ProvenanceWhy(motivation="untangling"),
        sources=[],
        targets=[],
    )
    return base_provenance


def is_paragraph(text_region: PageXMLTextRegion) -> bool:
    return text_region.type[-1] == "paragraph"


def is_magrginalium(text_region: PageXMLTextRegion) -> bool:
    return text_region.type[-1] == "marginalia"


def untangle_scan_doc(scan_doc: PageXMLScan, scan_start_anchor: int, path: str) -> Tuple[List[str], List[Annotation]]:
    scan_lines = []
    scan_annotations = []
    id_prefix = gt.make_id_prefix(scan_doc)

    for tr in scan_doc.get_text_regions_in_reading_order():
        tr_start_anchor = scan_start_anchor + len(scan_lines)
        tr_lines = []
        for line in tr.lines:
            if line.text:
                line_start_anchor = tr_start_anchor + len(tr_lines)
                tr_lines.append(line)
                # simple_annotation = SimpleAnnotation(type='TextLine', text=line.text, first_anchor=line_start_anchor,
                #                                      last_anchor=line_start_anchor, coords=line.coords,
                #                                      metadata={'id': line.id})
                px_line = gt.PXTextLine(
                    id=line.id,
                    text_region_id=tr.id,
                    page_id=page_id(scan_doc),
                    coords=line.coords,
                    first_word_id=None,
                    last_word_id=None,
                    text=line.text,
                )
                scan_annotations.append(
                    gt.text_line_annotation(text_line=px_line, id_prefix=id_prefix,
                                            offset=tr_start_anchor + len(tr_lines) - 1, length=1)
                )
        if tr_lines:
            px_textregion = gt.PXTextRegion(
                id=tr.id,
                page_id=page_id(scan_doc),
                coords=tr.coords,
                first_line_id=tr_lines[0].id,
                last_line_id=tr_lines[-1].id,
                first_word_id=None,
                last_word_id=None,
                segment_length=len(tr_lines),
                structure_type=tr.type[-1],
                text=" ".join([trl.text for trl in tr_lines])
            )
            scan_annotations.append(
                gt.text_region_annotation(text_region=px_textregion, id_prefix=id_prefix, offset=tr_start_anchor,
                                          length=len(tr_lines))
            )
            scan_lines.extend([trl.text for trl in tr_lines])

    scan_annotations.append(
        gt.page_annotation(id_prefix=id_prefix,
                           page_id=page_id(scan_doc),
                           path=path,
                           total_size=len(scan_lines),
                           document_id=scan_doc.id)
    )
    return scan_lines, scan_annotations


def page_id(scan_doc):
    return scan_doc.id.replace('.jpg', '')


def untangle_na_file(
        document_id: str,
        textrepo_client: TextRepoClient,
        pagexml_ids: List[str],
        base_provenance: ProvenanceData,
        links: Dict[str, Any]
) -> Tuple[Dict[str, any], ProvenanceData, List[Annotation]]:
    provenance = dataclasses.replace(base_provenance, sources=[], targets=[])

    scan_links = {}
    output_directory = f'out/{document_id}'
    os.makedirs(output_directory, exist_ok=True)
    document_lines = []
    document_annotations = []
    for external_id in pagexml_ids:
        page_links = {}
        page_xml_path = download_page_xml(external_id, textrepo_client, output_directory)
        version_identifier = textrepo_client.find_latest_version(external_id, "pagexml")
        version_location = textrepo_client.version_uri(version_identifier.id)
        provenance.sources.append(ProvenanceResource(resource=URI(version_location), relation="primary"))

        iiif_url = get_iiif_url(external_id, textrepo_client)
        if not iiif_url:
            links['errors'].append(f"{external_id}: missing scan_url")
        else:
            # logger.info(f"iiif_url={iiif_url}")
            page_links['iiif_url'] = iiif_url
            # page_links['paragraph_iiif_urls'] = []
            # page_links['sentences'] = []
            logger.info(f"<= {page_xml_path}")
            scan_doc: PageXMLScan = parse_pagexml_file(page_xml_path)
            start_offset = len(document_lines)
            scan_lines, scan_annotations = untangle_scan_doc(
                scan_doc=scan_doc,
                scan_start_anchor=start_offset,
                path=page_xml_path.split('/')[-1]
            )
            document_annotations.extend(scan_annotations)

            if not scan_lines:
                logger.warning(f"no paragraph text found in {page_xml_path}")
            else:
                document_lines.extend(scan_lines)
            scan_links[external_id] = page_links

    document_annotations.sort(key=lambda a: f"{a.page_id} {a.offset:06d} {(1000 - a.length):06d}")
    links['scan_links'] = scan_links
    segmented_text = {"_ordered_segments": document_lines}
    return segmented_text, provenance, document_annotations


def get_iiif_url(external_id, textrepo_client):
    document_metadata = textrepo_client.find_document_metadata(external_id)
    meta = document_metadata[1]
    if 'scan_url' in meta:
        scan_url = meta['scan_url']
        return f"{scan_url}/full/max/0/default.jpg"
    else:
        logger.error(f'{external_id}: missing scan_url in {meta}')
        ic(document_metadata)
        return ""


def download_page_xml(external_id, textrepo_client, output_directory: str):
    page_xml_path = f"{output_directory}/{external_id}.xml"
    if not Path(page_xml_path).is_file():
        pagexml = textrepo_client.find_latest_file_contents(external_id, "pagexml").decode('utf8')
        logger.info(f"=> {page_xml_path}")
        with open(page_xml_path, "w") as f:
            f.write(pagexml)
    return page_xml_path


def store_results(results: Dict[str, any]):
    path = "out/results.json"
    logger.info(f"=> {path}")
    with open(path, 'w') as f:
        json.dump(results, fp=f, cls=AnnotationEncoder, indent=4, ensure_ascii=False)


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


def read_na_file_metadata(selection_file: str) -> List[DocumentMetadata]:
    logger.info(f"<= {selection_file}")
    with open(selection_file, encoding='utf8') as f:
        reader = csv.DictReader(f)
        metadata = [to_document_metadata(row) for row in reader]
    return metadata


def create_or_update_tr_document(metadata: DocumentMetadata, client: TextRepoClient):
    document_identifier = client.read_document_by_external_id(metadata.external_id)
    if not document_identifier:
        document_identifier = client.create_document(external_id=metadata.external_id)
    document_id = document_identifier.id
    # client.set_document_metadata(document_id=document_id, key='title', value=metadata.title)
    # client.set_document_metadata(document_id=document_id, key='year_creation_or_dispatch',
    #                              value=metadata.year_creation_or_dispatch)
    client.set_document_metadata(document_id=document_id, key='inventory_number',
                                 value=metadata.inventory_number)
    # client.set_document_metadata(document_id=document_id, key='folio_or_page', value=metadata.folio_or_page)
    # client.set_document_metadata(document_id=document_id, key='folio_or_page_range',
    #                              value=metadata.folio_or_page_range)
    client.set_document_metadata(document_id=document_id, key='scan_range', value=metadata.scan_range)
    client.set_document_metadata(document_id=document_id, key='scan_start', value=metadata.scan_start)
    client.set_document_metadata(document_id=document_id, key='scan_end', value=metadata.scan_end)
    client.set_document_metadata(document_id=document_id, key='no_of_scans', value=str(metadata.no_of_scans))
    # client.set_document_metadata(document_id=document_id, key='no_of_pages', value=str(metadata.no_of_pages))
    # client.set_document_metadata(document_id=document_id, key='GM_id', value=metadata.GM_id)
    # client.set_document_metadata(document_id=document_id, key='remarks', value=metadata.remarks)
    return document_identifier


if __name__ == '__main__':
    main()
