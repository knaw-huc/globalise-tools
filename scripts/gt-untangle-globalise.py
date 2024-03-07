#!/usr/bin/env python3
import csv
import glob
import json
import os
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime
from random import shuffle
from typing import Tuple, List, Dict, Any, Union

import hydra
import pagexml.helper.pagexml_helper as pxh
from loguru import logger
from omegaconf import DictConfig
from pagexml.model.physical_document_model import PageXMLTextRegion, PageXMLScan
from pagexml.parser import parse_pagexml_file
from provenance.client import ProvenanceClient, ProvenanceData, ProvenanceHow, ProvenanceWhy
from textrepo.client import TextRepoClient
from uri import URI

import globalise_tools.tools as gt
from globalise_tools.model import AnnotationEncoder, WebAnnotation, DocumentMetadata2, DocumentMetadata, \
    LogicalAnchorRange, SegmentedTextType
from globalise_tools.tools import WebAnnotationFactory, Annotation

word_break_chars = '„'


@hydra.main(version_base=None)
@logger.catch
def main(cfg: DictConfig) -> None:
    # logger.level('warning')
    results = {}
    processed = load_processed_files()

    scan_url_mapping = read_scan_url_mapping()

    # metadata = read_all_metadata()
    metadata = read_na_file_metadata(cfg.documents_file)
    # base_provenance = generate_base_provenance(cfg)
    base_provenance = None
    textrepo_client = TextRepoClient(cfg.textrepo.base_uri, api_key=cfg.textrepo.api_key, verbose=False)
    check_file_types(textrepo_client)
    provenance_client = ProvenanceClient(base_url=cfg.provenance.base_uri, api_key=cfg.provenance.api_key)

    with open('data/na_file_selection.json') as f:
        na_file_id_selection = set(json.load(f))
    # # ic(list(na_file_id_selection)[0])
    # # ic(metadata[0].external_id)
    available_inv_nrs = get_available_inv_nrs()
    # dm_selection = [m for m in metadata if
    #                 m.nl_hana_nr in na_file_id_selection and m.external_id not in processed and m.inventory_number in available_inv_nrs]
    dm_selection = [m for m in metadata if m.inventory_number in available_inv_nrs][0:1]
    # dm_selection = [m for m in metadata if m.external_id not in processed and m.inventory_number in available_inv_nrs]
    shuffle(dm_selection)
    # dm_selection.sort(key=lambda x: x.no_of_scans)
    # dm_selection = sorted(metadata, key=lambda x: x.no_of_scans)[10:15]
    # dm_selection = metadata
    webannotation_factory = WebAnnotationFactory(cfg.iiif_mapping_file, cfg.textrepo.base_uri)

    total = len(dm_selection)
    with textrepo_client as trc, provenance_client as prc:
        for i, document_metadata in enumerate(dm_selection):
            logger.info(f"processing {document_metadata.external_id} [{i + 1}/{total}]")
            before = time.perf_counter()
            annotations_stored = process_na_file(document_metadata, base_provenance, prc, trc, webannotation_factory,
                                                 scan_url_mapping, results)
            after = time.perf_counter()
            diff = after - before
            logger.debug(f"done in {diff} s = {diff / document_metadata.no_of_scans} s/pagexml")
            if annotations_stored and not results[document_metadata.external_id]['errors']:
                processed.add(document_metadata.external_id)
                with open("out/processed.json", "w") as f:
                    json.dump(list(processed), fp=f)


def get_available_inv_nrs():
    inv_nr_paths = glob.glob("/Users/bram/workspaces/globalise/pagexml/*/")
    return set([p.split('/')[-2] for p in inv_nr_paths])


def read_all_metadata():
    path = f"data/pagexml_map.json"
    logger.info(f"<= {path}")
    with open(path, encoding='utf8') as f:
        pagexml_per_inv_nr = json.load(f)
    metadata = []
    for k in pagexml_per_inv_nr.keys():
        metadata.append(
            DocumentMetadata2(
                inventory_number=k,
                pagexml_ids=pagexml_per_inv_nr[k]
            )
        )
    return metadata


def read_scan_url_mapping() -> Dict[str, str]:
    path = "data/scan_url_mapping.json"
    with open(path) as f:
        scan_url_mapping = json.load(f)
    return scan_url_mapping


def load_processed_files():
    processed_file = "out/processed.json"
    if os.path.exists(processed_file):
        logger.info(f"<= {processed_file}")
        with open(processed_file) as f:
            processed = set(json.load(f))
    else:
        processed = set()
    return processed


def process_na_file(
        document_metadata: DocumentMetadata,
        base_provenance: ProvenanceData,
        prov_client: ProvenanceClient,
        tr_client: TextRepoClient,
        waf: WebAnnotationFactory,
        scan_url_mapping: Dict[str, str],
        results: Dict[str, any]
) -> bool:
    links = {'textrepo_links': {}, 'errors': []}

    document_identifier = create_or_update_tr_document(document_metadata, tr_client)

    links['textrepo_links']['document'] = f"{tr_client.base_uri}/rest/documents/{document_identifier.id}"
    links['textrepo_links']['metadata'] = f"{tr_client.base_uri}/rest/documents/{document_identifier.id}/metadata"

    physical_segmented_text, logical_segmented_text, text_provenance, annotations = untangle_na_file(
        document_id=document_metadata.nl_hana_nr,
        textrepo_client=tr_client,
        pagexml_ids=document_metadata.pagexml_ids,
        base_provenance=base_provenance,
        links=links,
        scan_url_mapping=scan_url_mapping
    )
    physical_version_identifier = store_segmented_text(physical_segmented_text, SegmentedTextType.PHYSICAL,
                                                       document_metadata, tr_client,
                                                       links)
    logical_version_identifier = store_segmented_text(logical_segmented_text, SegmentedTextType.LOGICAL,
                                                      document_metadata, tr_client,
                                                      links)
    # # provenance = dataclasses.replace(
    # #     base_provenance,
    # #     sources=[ProvenanceResource(resource=URI(version_uri), relation='primary')],
    # #     targets=[ProvenanceResource(resource=URI(inception_view), relation='primary')],
    # # )
    # text_provenance_id = prov_client.add_provenance(text_provenance)
    # # provenance_id = prc.add_provenance(provenance)
    # prov_json_link = str(text_provenance_id.location)
    # prov_html_link = prov_json_link.replace('prov/', '#')
    # links['provenance_links'] = [prov_json_link, prov_html_link]
    results[document_metadata.external_id] = links

    store_results(results)

    if annotations:
        for a in annotations:
            a.physical_span.textrepo_version_id = physical_version_identifier.version_id
            a.physical_span.begin_anchor = a.physical_span.offset
            a.physical_span.end_anchor = a.physical_span.offset + a.physical_span.length - 1
            a.logical_span.textrepo_version_id = logical_version_identifier.version_id
            if not a.type == 'px:TextLine':
                a.logical_span.begin_anchor = a.logical_span.offset
                a.logical_span.end_anchor = a.logical_span.offset + a.logical_span.length - 1

        web_annotations = [to_web_annotation(a, webannotation_factory=waf) for a in annotations]
        web_annotations.insert(
            0,
            document_web_annotation(annotations, document_metadata.nl_hana_nr, document_metadata.inventory_number, waf,
                                    physical_version_identifier.version_id, logical_version_identifier.version_id)
        )

        export_web_annotations(document_metadata, web_annotations)
    return len(annotations) > 0


def store_segmented_text(segmented_text, segmented_text_type: SegmentedTextType, document_metadata, tr_client, links):
    if segmented_text_type == SegmentedTextType.PHYSICAL:
        type_name = 'segmented_text'
        prefix = 'physical'
    else:
        type_name = 'logical_segmented_text'
        prefix = 'logical'

    version_identifier = tr_client.import_version(
        external_id=document_metadata.external_id,
        type_name=type_name,
        contents=json.dumps(segmented_text, ensure_ascii=False),
        as_latest_version=True
    )
    links['textrepo_links'][prefix] = {}
    links['textrepo_links'][prefix]['file'] = f"{tr_client.base_uri}/rest/files/{version_identifier.file_id}"
    version_uri = f"{tr_client.base_uri}/rest/versions/{version_identifier.version_id}"
    links['textrepo_links'][prefix]['version'] = version_uri
    # text_provenance.targets.append(ProvenanceResource(resource=URI(version_uri), relation="primary"))
    links['textrepo_links'][prefix]['contents'] = (f"{tr_client.base_uri}/task/find/{document_metadata.external_id}"
                                                   f"/file/contents?type={type_name}")
    file_name = f'{document_metadata.nl_hana_nr}-{prefix}.json'
    tr_client.set_file_metadata(file_id=version_identifier.file_id, key='file_name', value=file_name)
    return version_identifier


def to_web_annotation(annotation: Annotation,
                      webannotation_factory: WebAnnotationFactory) -> WebAnnotation:
    body_id = annotation.id
    if 'text' in annotation.metadata:
        annotation.metadata.pop('text')
    body = {
        "id": body_id,
        "type": annotation.type,
        "metadata": annotation.metadata
    }
    targets = webannotation_factory.annotation_targets(annotation)
    body['metadata'].pop("coords", None)
    return WebAnnotation(body=body, target=targets)


def document_web_annotation(all_annotations: List[Annotation], document_id: str, inventory_number: str,
                            webannotation_factory: WebAnnotationFactory, physical_segmented_version_id: str,
                            logical_segmented_version_id: str) -> WebAnnotation:
    manifest_url = f"https://data.globalise.huygens.knaw.nl/manifests/inventories/{inventory_number}.json"
    physical_end_anchor = max([a.physical_span.end_anchor for a in all_annotations])
    logical_end_anchor = max([a.logical_span.end_anchor for a in all_annotations])
    return WebAnnotation(
        body={
            "@context": {"na": "https://knaw-huc.github.io/ns/nationaal-archief#",
                         "@vocab": "https://knaw-huc.github.io/ns/globalise#"},
            "id": f"urn:globalise:{document_id}:file",
            "type": "na:File",
            "metadata": {
                "type": "na:FileMetadata",
                "file": document_id,
                "inventoryNumber": inventory_number,
                "manifest": manifest_url
            }
        },
        target=[
            webannotation_factory.physical_text_anchor_selector_target(
                text_span=gt.TextSpan(
                    textrepo_version_id=physical_segmented_version_id,
                    begin_anchor=0,
                    end_anchor=physical_end_anchor
                )),
            webannotation_factory.physical_text_cutout_target(
                text_span=gt.TextSpan(
                    textrepo_version_id=physical_segmented_version_id,
                    begin_anchor=0,
                    end_anchor=physical_end_anchor
                )),
            webannotation_factory.logical_text_anchor_selector_target(
                text_span=gt.TextSpan(
                    textrepo_version_id=logical_segmented_version_id,
                    begin_anchor=0,
                    end_anchor=logical_end_anchor
                )),
            webannotation_factory.logical_text_cutout_target(
                text_span=gt.TextSpan(
                    textrepo_version_id=logical_segmented_version_id,
                    begin_anchor=0,
                    end_anchor=logical_end_anchor
                ))
        ]
    )


def export_web_annotations(document_metadata, web_annotations):
    path = f"out/{document_metadata.nl_hana_nr}/web_annotations.json"
    logger.debug(f"=> {path}")
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


def is_marginalia(text_region: PageXMLTextRegion) -> bool:
    return text_region.type[-1] == "marginalia"


general_text_region_types = ['physical_structure_doc', 'pagexml_doc', 'text_region']


def defining_text_region_type(types) -> str:
    return "/".join([t for t in types if t not in general_text_region_types])


def untangle_scan_doc(
        scan_doc: PageXMLScan,
        physical_start_anchor: int,
        path: str,
        line_ids_to_anchors: Dict[str, int],
        logical_anchor_range_for_line_id: Dict[str, LogicalAnchorRange],
        paragraphs: List[str]
) -> tuple[list[Union[str, Any]], list[Annotation]]:
    logical_start_anchor = len(paragraphs)
    scan_lines = []
    scan_annotations = []
    id_prefix = gt.make_id_prefix(scan_doc)
    for tr in scan_doc.get_text_regions_in_reading_order():
        tr_start_anchor = physical_start_anchor + len(scan_lines)
        tr_lines = []
        lines_with_text = [line for line in tr.lines if line.text]
        for line in lines_with_text:
            line_ids_to_anchors[line.id] = physical_start_anchor + len(tr_lines)
            tr_lines.append(line)
            # simple_annotation = SimpleAnnotation(type='TextLine', text=line.text, first_anchor=line_start_anchor,
            #                                      last_anchor=line_start_anchor, coords=line.coords,
            #                                      metadata={'id': line.id})
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
                structure_type=defining_text_region_type(tr.type),
                text=" ".join([trl.text for trl in tr_lines])
            )
            scan_annotations.append(
                gt.text_region_annotation(text_region=px_textregion, id_prefix=id_prefix,
                                          physical_span=gt.TextSpan(offset=tr_start_anchor,
                                                                    length=len(tr_lines)),
                                          logical_span=gt.TextSpan(offset=len(paragraphs), length=1))
            )
            scan_lines.extend([trl.text for trl in tr_lines])
            tr_text, line_ranges = pxh.make_text_region_text(lines_with_text, word_break_chars=word_break_chars)
            para_anchor = len(paragraphs)
            for line_range in line_ranges:
                start = line_range['start']
                end = line_range['end']
                logical_anchor_range_for_line_id[line_range['line_id']] = LogicalAnchorRange(
                    begin_logical_anchor=para_anchor,
                    begin_char_offset=start,
                    end_logical_anchor=para_anchor,
                    end_char_offset=end
                )
                if start > end:
                    logger.error(f"start {start} > end {end}")
            paragraphs.append(tr_text)

            for n, line in enumerate(tr_lines):
                line_start_anchor = tr_start_anchor + n
                logical_anchor_range = logical_anchor_range_for_line_id[line.id]
                px_line = gt.PXTextLine(
                    id=line.id,
                    text_region_id=tr.id,
                    page_id=page_id(scan_doc),
                    coords=line.coords,
                    first_word_id=None,
                    last_word_id=None,
                    text=line.text,
                )
                physical_span = gt.TextSpan(offset=line_start_anchor, length=1)
                logical_span = gt.TextSpan(begin_anchor=logical_anchor_range.begin_logical_anchor,
                                           char_start=logical_anchor_range.begin_char_offset,
                                           end_anchor=logical_anchor_range.end_logical_anchor,
                                           char_end=logical_anchor_range.end_char_offset)
                scan_annotations.append(
                    gt.text_line_annotation(
                        text_line=px_line,
                        id_prefix=id_prefix,
                        physical_span=physical_span,
                        logical_span=logical_span
                    )
                )

    if not scan_lines:
        logger.warning(f"no paragraph text found in {scan_doc.id.replace('.jpg', '')}")
        scan_lines.append("")
        paragraphs.append("")

    scan_annotations.append(
        gt.page_annotation(id_prefix=id_prefix,
                           page_id=page_id(scan_doc),
                           scan_doc_metadata=scan_doc.metadata,
                           path=path,
                           physical_span=gt.TextSpan(offset=physical_start_anchor, length=len(scan_lines)),
                           logical_span=gt.TextSpan(offset=logical_start_anchor,
                                                    length=len(paragraphs) - logical_start_anchor),
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
        links: Dict[str, Any],
        scan_url_mapping: Dict[str, str]
) -> Tuple[Dict[str, any], Dict[str, any], ProvenanceData, List[Annotation]]:
    # provenance = dataclasses.replace(base_provenance, sources=[], targets=[])
    provenance = None

    # scan_links = {}
    output_directory = f'out/{document_id}'
    os.makedirs(output_directory, exist_ok=True)
    document_lines = []
    line_ids_to_anchors = {}
    logical_anchor_range_for_line_id = defaultdict(lambda: LogicalAnchorRange(0, 0, 0, 0))
    document_paragraphs = []
    document_annotations = []
    total = len(pagexml_ids)
    logger.info(f"processing {total} pagexmls...")
    for external_id in pagexml_ids:
        page_links = {}
        tries = 0
        done = False
        while not done:
            # page_xml_path, page_xml, error = download_page_xml(external_id, textrepo_client, output_directory)
            page_xml_path, page_xml, error = read_page_xml(external_id)
            if error and tries < 10:
                logger.error(f"Error={error}")
                tries += 1
                logger.warning(f"error returned on downloading {external_id}, retry in {tries} seconds")
                time.sleep(tries)
                done = False
            else:
                done = True

        if error:
            links['errors'].append(error)
        else:
            # version_identifier = textrepo_client.find_latest_version(external_id, "pagexml")
            # version_location = textrepo_client.version_uri(version_identifier.id)
            # provenance.sources.append(ProvenanceResource(resource=URI(version_location), relation="primary"))

            if external_id not in scan_url_mapping:
                links['errors'].append(f"{external_id}: missing scan_url")
            else:
                iiif_url = scan_url_mapping[external_id]
                # logger.info(f"iiif_url={iiif_url}")
                page_links['iiif_url'] = iiif_url
                # page_links['paragraph_iiif_urls'] = []
                # page_links['sentences'] = []
                # logger.info(f"<= {page_xml_path}")
                scan_doc: PageXMLScan = parse_pagexml_file(pagexml_file=page_xml_path, pagexml_data=page_xml)
                start_offset = len(document_lines)
                scan_lines, scan_annotations = untangle_scan_doc(
                    scan_doc=scan_doc,
                    physical_start_anchor=start_offset,
                    path=page_xml_path.split('/')[-1],
                    line_ids_to_anchors=line_ids_to_anchors,
                    paragraphs=document_paragraphs,
                    logical_anchor_range_for_line_id=logical_anchor_range_for_line_id
                )
                document_annotations.extend(scan_annotations)
                document_lines.extend(scan_lines)
                # scan_links[external_id] = page_links
                # os.remove(page_xml_path)

    document_annotations.sort(
        key=lambda a: f"{a.page_id} {a.physical_span.offset:06d} {(1000 - a.physical_span.length):06d}")
    # links['scan_links'] = scan_links
    physical_segmented_text = {"_ordered_segments": document_lines}
    logical_segmented_text = {"_ordered_segments": document_paragraphs}
    return physical_segmented_text, logical_segmented_text, provenance, document_annotations


def read_page_xml(external_id):
    inv_nr = external_id.split('_')[-2]
    page_xml_dir = "/Users/bram/workspaces/globalise/pagexml"
    page_xml_path = f"{page_xml_dir}/{inv_nr}/{external_id}.xml"
    with open(page_xml_path) as f:
        page_xml = f.read()
    error = []
    return page_xml_path, page_xml, error


def get_iiif_url(external_id, textrepo_client):
    document_metadata = textrepo_client.find_document_metadata(external_id)
    meta = document_metadata[1]
    if 'scan_url' in meta:
        scan_url = meta['scan_url']
        return f"{scan_url}/full/max/0/default.jpg"
    else:
        logger.error(f'{external_id}: missing scan_url in {meta}')
        # ic(document_metadata)
        return ""


def download_page_xml(external_id, textrepo_client, output_directory: str):
    error = None
    page_xml_path = f"{output_directory}/{external_id}.xml"
    # if not Path(page_xml_path).is_file():
    try:
        page_xml = textrepo_client.find_latest_file_contents(external_id, "pagexml").decode('utf8')
        # logger.info(f"=> {page_xml_path}")
        # with open(page_xml_path, "w") as f:
        #     f.write(pagexml)
    except:
        error = f"{external_id}: not found on {textrepo_client.base_uri}"
        logger.error(error)
    return page_xml_path, page_xml, error


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
        # metadata = [to_document_metadata(row) for row in reader if row['Quality Check'] == 'TRUE']
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


def check_file_types(trc):
    name = "logical_segmented_text"
    available_type_names = [t.name for t in trc.read_file_types()]
    if name not in available_type_names:
        trc.create_file_type(name=name, mimetype="application/json")


if __name__ == '__main__':
    main()
