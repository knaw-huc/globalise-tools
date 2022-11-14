#!/usr/bin/env python3
import argparse
import itertools
import json
import os
from dataclasses import dataclass
from json import JSONEncoder
from typing import List, AnyStr, Dict, Any

import pagexml.parser as pxp
from dataclasses_json import dataclass_json
from pagexml.model.physical_document_model import PageXMLScan, Coords

import globalise_tools.tools as gt


@dataclass_json
@dataclass
class Annotation:
    type: str
    metadata: Dict[AnyStr, Any]
    offset: int
    length: int


class AnnotationEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Annotation):
            return obj.to_dict()
        elif isinstance(obj, gt.PXTextRegion):
            return obj.to_dict()
        elif isinstance(obj, gt.PXTextLine):
            return obj.to_dict()
        elif isinstance(obj, Coords):
            return obj.points


def list_pagexml_files(directory: str):
    all_files = os.listdir(directory)
    return sorted([f'{directory}/{f}' for f in all_files if f.endswith(".xml")])


def process_pagexml(path):
    annotations = []
    scan_doc: PageXMLScan = pxp.parse_pagexml_file(path)

    # lines = scan_doc.get_lines()
    # paragraphs = [line.text + "\n" for line in lines if line.text]

    px_words, tr_idx, tl_idx = gt.extract_pxwords(scan_doc)
    display_words = gt.to_display_words(px_words)
    text = ''
    for w in display_words:
        stripped = w.text.strip()
        annotations.append(
            Annotation(
                type="Word",
                offset=len(text),
                length=len(stripped),
                metadata={
                    "text": stripped,
                    "coords": [pxw.coords for pxw in w.px_words]
                }
            )
        )
        text += w.text

    # text = ''.join(w.text for w in display_words)
    paragraphs = [f'{p}\n' for p in text.split("\n")]
    total_size = len("".join(paragraphs))

    page_id = path.split('/')[-1].replace(".xml", "")
    annotations.append(
        Annotation(
            type="Page",
            offset=0,
            length=total_size,
            metadata={
                "id": page_id,
                "n": page_id.split("_")[-1],
                "file": path,
                "na_url": gt.na_url(path),
                "tr_url": gt.tr_url(path)
            }
        )
    )
    return paragraphs, annotations, total_size


def export(base_name: AnyStr, all_text: List[AnyStr], metadata: Dict[AnyStr, Any]):
    file_name = f"{base_name}.txt"
    print(f"exporting text to {file_name}")
    with open(file_name, 'w', encoding='utf-8') as f:
        f.writelines(all_text)

    metadata_file_name = f"{base_name}-metadata.json"
    print(f"exporting metadata to {metadata_file_name}")
    with open(metadata_file_name, 'w') as f:
        json.dump(metadata, f, indent=2, cls=AnnotationEncoder)


def process_directory_group(group_name: str, directory_group: str):
    pagexml_files = []
    for directory in directory_group:
        pagexml_files.extend(list_pagexml_files(directory))
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

    metadata = {"annotations": all_annotations}
    export(group_name, all_pars, metadata)


def main():
    parser = argparse.ArgumentParser(
        description="Extract text from all the PageXML in the given directory",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("directory",
                        help="A directory containing the PageXML files to extract the text from.",
                        nargs='+',
                        type=str)
    args = parser.parse_args()

    if args.directory:
        directories = args.directory
        groups = itertools.groupby(directories, lambda d: d.rstrip('/').split('/')[-1].split('_')[0])
        for key, group in groups:
            process_directory_group(key, group)


if __name__ == '__main__':
    main()
