#!/usr/bin/env python3
import argparse
import json
import os
from dataclasses import dataclass
from json import JSONEncoder
from typing import List, AnyStr, Dict, Any

from dataclasses_json import dataclass_json
from pagexml.parser import parse_pagexml_file


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


def list_pagexml_files(directory: str):
    all_files = os.listdir(directory)
    return sorted([f'{directory}/{f}' for f in all_files if f.endswith(".xml")])


def process_pagexml(path):
    annotations = []
    scan_doc = parse_pagexml_file(path)
    lines = scan_doc.get_lines()
    for line in lines:
        pass
    paragraphs = [line.text + "\n" for line in lines]
    total_size = len("".join(paragraphs))
    annotations.append(Annotation(type="Page", offset=0, length=total_size, metadata={"file": path}))
    return paragraphs, annotations


def export(base_name: AnyStr, all_text: List[AnyStr], metadata: Dict[AnyStr, Any]):
    file_name = f"{base_name}.txt"
    print(f"exporting text to {file_name}")
    with open(file_name, 'w') as f:
        f.writelines(all_text)
    metadata_file_name = f"{base_name}-metadata.json"
    print(f"exporting metadata to {metadata_file_name}")
    with open(metadata_file_name, 'w') as f:
        json.dump(metadata, f, indent=4, cls=AnnotationEncoder)


def main():
    parser = argparse.ArgumentParser(
        description="Extract text from all the PageXML in the given directory",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("directory",
                        help="The directory containing the PageXML files to extract the text from.",
                        type=str)
    args = parser.parse_args()

    if args.directory:
        directory = args.directory
        pagexml_files = list_pagexml_files(directory)
        all_pars = []
        all_annotations = []
        start_offset = 0
        for f in pagexml_files:
            (paragraphs, annotations) = process_pagexml(f)
            all_pars += paragraphs
            for annotation in annotations:
                annotation.offset += start_offset
                all_annotations.append(annotation)
            start_offset = start_offset + len("".join(paragraphs))
        base_name = directory.split('/')[-1]
        metadata = {"annotations": all_annotations}
        export(base_name, all_pars, metadata)


if __name__ == '__main__':
    main()
