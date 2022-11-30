#!/usr/bin/env python3
import argparse
import csv
import itertools
import json
import os
import uuid as uuid
from dataclasses import dataclass
from datetime import datetime
from json import JSONEncoder
from typing import List, AnyStr, Dict, Any

import pagexml.parser as pxp
import spacy
from dataclasses_json import dataclass_json
from pagexml.model.physical_document_model import PageXMLScan, Coords

import globalise_tools.tools as gt

spacy_core = "nl_core_news_lg"
metadata_csv = "data/metadata_1618-1793_2022-08-30.csv"
ground_truth_csv = "data/globalise-word-joins-MH.csv"
metadata_records = []
ground_truth = []


@dataclass_json
@dataclass
class Annotation:
    type: str
    metadata: Dict[AnyStr, Any]
    offset: int
    length: int


@dataclass
class WebAnnotation:
    body: Dict[str, Any]
    target: Any

    def wrapped(self):
        anno_uuid = uuid.uuid4()
        return {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "id": f"urn:globalise:annotation:{anno_uuid}",
            "type": "Annotation",
            "motivation": "classifying",
            "generated": datetime.today().isoformat(),  # use last-modified from pagexml for px: types
            "generator": {  # use creator metadata from pagexml for px: types
                "id": "https://github.com/rvankoert/loghi-htr",
                "type": "Software",
                "name": "Loghi"
            },
            "body": self.body,
            "target": self.target
        }


class AnnotationEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Annotation):
            return obj.to_dict()
        if isinstance(obj, WebAnnotation):
            return obj.wrapped()
        elif isinstance(obj, gt.PXTextRegion):
            return obj.to_dict()
        elif isinstance(obj, gt.PXTextLine):
            return obj.to_dict()
        elif isinstance(obj, Coords):
            return obj.points


def list_pagexml_files(directory: str):
    all_files = os.listdir(directory)
    return sorted([f'{directory}/{f}' for f in all_files if f.endswith(".xml")])


def make_id_prefix(scan_doc) -> str:
    return "urn:globalise:" + scan_doc.id.replace(".jpg", "")


def process_pagexml(path):
    annotations = []
    scan_doc: PageXMLScan = pxp.parse_pagexml_file(path)
    id_prefix = make_id_prefix(scan_doc)

    px_words, tr_idx, tl_idx = gt.extract_pxwords(scan_doc)
    display_words = gt.to_display_words(px_words)
    text = ''
    for w in display_words:
        stripped = w.text.strip()
        annotations.append(
            Annotation(
                type="tt:Word",
                offset=len(text),
                length=len(stripped),
                metadata={
                    "id": make_word_id(id_prefix, w),
                    "text": stripped,
                    "page_id": w.px_words[0].page_id,
                    "coords": [pxw.coords for pxw in w.px_words]
                }
            )
        )
        text += w.text

    paragraphs = [f'{p}\n' for p in text.split("\n")]
    total_size = len("".join(paragraphs))

    page_id = to_base_name(path)
    annotations.append(
        Annotation(
            type="px:Page",
            offset=0,
            length=total_size,
            metadata={
                "id": make_page_id(id_prefix, page_id),
                "page_id": page_id,
                "n": page_id.split("_")[-1],
                "file": path,
                "na_url": gt.na_url(path),
                "tr_url": gt.tr_url(path)
            }
        )
    )

    for text_region in tr_idx.values():
        offset = -1
        length = -1
        annotations.append(
            Annotation(
                type="px:TextRegion",
                offset=offset,
                length=length,
                metadata={
                    "id": make_textregion_id(id_prefix, text_region.id),
                    "page_id": text_region.page_id,
                    "coords": text_region.coords
                }
            )
        )

    for text_line in tl_idx.values():
        offset = -1
        length = -1
        annotations.append(
            Annotation(
                type="px:TextLine",
                offset=offset,
                length=length,
                metadata={
                    "id": make_textline_id(id_prefix, text_line.id),
                    "page_id": text_line.page_id,
                    "coords": text_line.coords
                }
            )
        )
    return paragraphs, annotations, total_size


def make_word_id(prefix: str, w) -> str:
    return prefix + ":word:" + ":".join([pxw.id for pxw in w.px_words])


def make_textline_id(prefix: str, line_id) -> str:
    return prefix + ":textline:" + line_id


def make_page_id(prefix: str, page_id) -> str:
    return prefix + ":page:" + page_id


def make_textregion_id(prefix: str, textregion_id) -> str:
    return prefix + ":textregion:" + textregion_id


def to_conll2002(token: str) -> str:
    return "\n" if token in ["", "\n"] else f"{token} O\n"


def as_conll2002(tokens: List[str]) -> List[str]:
    return [to_conll2002(t) for t in tokens]


def export(base_name: AnyStr,
           all_text: List[AnyStr],
           metadata: Dict[AnyStr, Any],
           tokens: List[str],
           token_offsets,
           web_annotations: List[WebAnnotation]
           ):
    print(f"{base_name}:")

    file_name = f"{base_name}.txt"
    print(f"exporting text to {file_name}")
    with open(file_name, 'w', encoding='utf-8') as f:
        f.writelines(all_text)

    file_name = f"{base_name}-tokens.json"
    print(f"exporting tokens to {file_name}")
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(tokens, f, indent=2)

    file_name = f"{base_name}.cnll"
    print(f"exporting tokens as CoNLL 2002 to {file_name}")
    with open(file_name, 'w', encoding='utf-8') as f:
        f.writelines(as_conll2002(tokens))

    metadata_file_name = f"{base_name}-metadata.json"
    print(f"exporting metadata to {metadata_file_name}")
    with open(metadata_file_name, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, cls=AnnotationEncoder)

    file_name = f"{base_name}-token-offsets.json"
    print(f"exporting token offsets to {file_name}")
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(token_offsets, f, indent=2, cls=AnnotationEncoder)

    file_name = f"{base_name}-web-annotations.json"
    print(f"exporting web annotations to {file_name}")
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(web_annotations, f, indent=2, cls=AnnotationEncoder)

    print()


def to_base_name(path: str) -> str:
    return path.split('/')[-1].replace(".xml", "")


def create_base_name(pagexml_files: List[str]) -> str:
    first = to_base_name(pagexml_files[0])
    last = to_base_name(pagexml_files[-1])
    i = first.rindex("_")
    base = first[0:i]
    first_page = first[i + 1:]
    last_page = last[i + 1:]
    return f"{base}_{first_page}_{last_page}"


def tokenize(all_pars: List[str]) -> (List[str], List[int]):
    tokens = []
    offsets = []
    text = ''.join(all_pars)
    doc = nlp(text)
    for sentence in doc.sents:
        for token in [t for t in sentence if t.text != "\n"]:
            tokens.append(token.text)
            offsets.append(token.idx)
        tokens.append("")
        offsets.append(-1)
    return tokens, offsets


def read_metadata(basename: str) -> Dict[str, str]:
    (_a, _b, index_nr, scan_nr) = basename.split("_")
    scan = int(scan_nr)
    relevant = [r for r in metadata_records if
                r['Indexnr'] == index_nr and int(r['Scan-begin']) <= scan <= int(r['Scan-Eind'])]
    if len(relevant) > 1:
        raise ">1 metadata records relevant"
    else:
        return relevant[0]


def make_token_annotations(base_name, tokens, token_offsets):
    annotations = []
    sentence_offset = 0
    sentence_length = 0
    sentence_num = 1
    page_id = ":TODO:"
    for i, pair in enumerate(zip(tokens, token_offsets)):
        (token, offset) = pair
        token_is_sentence_end = offset < 0
        if token_is_sentence_end:
            annotations.append(Annotation(
                type="tt:Sentence",
                offset=sentence_offset,
                length=sentence_length,
                metadata={
                    "id": f"urn:globalise:{base_name}:sentence:{sentence_num}",
                    "page_id": page_id
                }
            ))
            sentence_offset += sentence_length
            sentence_num += 1
        else:
            token_length = len(token)
            annotations.append(Annotation(
                type="tt:Token",
                offset=offset,
                length=token_length,
                metadata={
                    "id": f"urn:globalise:{base_name}:token:{i}",
                    "page_id": page_id
                }
            ))
            sentence_length = offset - sentence_offset + token_length
    return annotations


iiif_base_url_idx = {}


def init_iiif_base_url_idx(path: str):
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            iiif_base_url_idx[row["pagexml_id"]] = row["iiif_base_url"]


def get_iiif_base_url(page_id: str) -> str:
    return iiif_base_url_idx[page_id]


def make_image_targets(page_id: str, coords: List[Coords]) -> List[Dict[str, Any]]:
    targets = []
    iiif_base_url = get_iiif_base_url(page_id)
    iiif_url = f"{iiif_base_url}/full/max/0/default.jpg"
    for c in coords:
        xywh = f"{c.box['x']},{c.box['y']},{c.box['w']},{c.box['h']}"
        target = {
            "source": iiif_url,
            "type": "Image",
            "selector": {
                "type": "FragmentSelector",
                "conformsTo": "http://www.w3.org/TR/media-frags/",
                "value": f"xywh={xywh}"
            }
        }
        targets.append(target)

        target = {
            "source": f"{iiif_base_url}/{xywh}/max/0/default.jpg",
            "type": "Image"
        }
        targets.append(target)

    svg_target = image_target_wth_svg_selector(iiif_url, [c.points for c in coords])
    targets.append(svg_target)

    return targets


def canvas_target(canvas_url: str, xywh_list: List[str] = None, coords_list: List[List[List[int]]] = None) -> dict:
    selectors = []
    if xywh_list:
        for xywh in xywh_list:
            selectors.append({
                "@context": "http://iiif.io/api/annex/openannotation/context.json",
                "type": "iiif:ImageApiSelector",
                "region": xywh
            })
    if coords_list:
        selectors.append(svg_selector(coords_list))
    return {
        '@context': "https://brambg.github.io/ns/republic.jsonld",
        'source': canvas_url,
        'type': "Canvas",
        'selector': selectors
    }


def svg_selector(coords_list):
    path_defs = []
    height = 0
    width = 0
    for coords in coords_list:
        height = max(height, max([c[1] for c in coords]))
        width = max(width, max([c[0] for c in coords]))
        path_def = ' '.join([f"L{c[0]} {c[1]}" for c in coords]) + " Z"
        path_def = 'M' + path_def[1:]
        path_defs.append(path_def)
    path = f"""<path d="{' '.join(path_defs)}"/>"""
    return {'type': "SvgSelector", 'value': f"""<svg height="{height}" width="{width}">{path}</svg>"""}


def image_target_wth_svg_selector(iiif_url: str,
                                  coords_list: List) -> dict:
    return {'source': iiif_url, 'type': "Image", 'selector': svg_selector(coords_list)}


def to_web_annotation(annotation: Annotation) -> WebAnnotation:
    body = annotation_body(annotation)
    targets = annotation_targets(annotation)
    return WebAnnotation(body=body, target=targets)


def annotation_body(annotation):
    body = {
        "@context": {"tt": "https://brambg.github.io/ns/team-text#", "px": "https://brambg.github.io/ns/pagexml#"},
        "id": annotation.metadata["id"],
        "type": annotation.type
    }
    if "text" in annotation.metadata:
        body["text"] = annotation.metadata["text"]
    return body


def text_targets():
    return []


def to_xywh(coords: Coords):
    return f"{coords.left},{coords.top},{coords.width},{coords.height}"


def annotation_targets(annotation):
    targets = []
    page_id = annotation.metadata["page_id"]
    if "coords" in annotation.metadata:
        page_id = annotation.metadata["page_id"]
        coords = annotation.metadata["coords"]
        if isinstance(coords, Coords):
            coords = [coords]
        targets.extend(make_image_targets(page_id, coords))
        canvas_url = f"urn:globalise:canvas:{page_id}"
        xywh_list = [to_xywh(c) for c in coords]
        points = [c.points for c in coords]
        targets.append(canvas_target(canvas_url=canvas_url, xywh_list=xywh_list, coords_list=points))
    if annotation.type == "px:Page":
        iiif_base_url = get_iiif_base_url(page_id)
        iiif_url = f"{iiif_base_url}/full/max/0/default.jpg"
        targets.append({
            "source": iiif_url,
            "type": "Image"
        })
    targets.extend(text_targets())
    return targets


def make_web_annotations(annotations: List[Annotation]) -> List[WebAnnotation]:
    return [to_web_annotation(a) for a in annotations]


def process_directory_group(directory_group: List[str]):
    pagexml_files = []
    for directory in directory_group:
        pagexml_files.extend(list_pagexml_files(directory))
    pagexml_files.sort()

    base_name = create_base_name(pagexml_files)

    all_pars = []
    all_annotations = []
    start_offset = 0
    for f in pagexml_files:
        (paragraphs, annotations, par_length) = process_pagexml(f)
        all_pars += paragraphs
        for annotation in annotations:
            annotation.offset += start_offset
            all_annotations.append(annotation)
        start_offset = start_offset + par_length

    (tokens, token_offsets) = tokenize(all_pars)
    token_annotations = make_token_annotations(base_name, tokens, token_offsets)
    all_annotations.extend(token_annotations)

    metadata = read_metadata(to_base_name(pagexml_files[0]))
    metadata.update({
        "tanap_vestiging": "Batavia",
        "tanap_jaar": 1684,
        "annotations": all_annotations,
    })
    web_annotations = make_web_annotations(all_annotations)
    export(base_name, all_pars, metadata, tokens, token_offsets, web_annotations)


def init_spacy():
    global nlp
    nlp = spacy.load(spacy_core)


def load_metadata():
    with open(metadata_csv) as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            metadata_records.append(row)


def load_ground_truth():
    records = []
    with open(ground_truth_csv) as f:
        reader = csv.DictReader(f)
        for row in enumerate(reader):
            records.append(row)
    ground_truth.extend([(r['scan'], r['line n'], r['line n+1']) for r in records if r['join?'] != ''])


def get_arguments():
    parser = argparse.ArgumentParser(
        description="Extract text and annotations from all the PageXML in the given directory",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i",
                        "--iiif-mapping-file",
                        required=True,
                        help="The path to the file mapping pagexml id to iiif base url",
                        type=str)
    parser.add_argument("-m",
                        "--merge-sections",
                        required=False,
                        help="Set this to merge sections into one document",
                        action="store_true")
    parser.add_argument("directory",
                        help="A directory containing the PageXML files to extract the text from.",
                        nargs='+',
                        type=str)
    return parser.parse_args()


def main():
    args = get_arguments()
    if args.directory:
        init_iiif_base_url_idx(args.iiif_mapping_file)
        init_spacy()
        load_metadata()
        load_ground_truth()
        directories = args.directory
        if args.merge_sections:
            groups = itertools.groupby(directories, lambda d: d.rstrip('/').split('/')[-1].split('_')[0])
            for key, group in groups:
                process_directory_group(group)
        else:
            for d in directories:
                process_directory_group([d])


if __name__ == '__main__':
    main()
