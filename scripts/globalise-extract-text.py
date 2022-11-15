#!/usr/bin/env python3
import argparse
import itertools
import json
import os
from dataclasses import dataclass
from json import JSONEncoder
from typing import List, AnyStr, Dict, Any

import pagexml.parser as pxp
import spacy
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

    paragraphs = [f'{p}\n' for p in text.split("\n")]
    total_size = len("".join(paragraphs))

    page_id = to_base_name(path)
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


def to_conll2002(token: str) -> str:
    return "\n" if token in ["", "\n"] else f"{token} O\n"


def as_conll2002(tokens: List[str]) -> List[str]:
    return [to_conll2002(t) for t in tokens]


def export(base_name: AnyStr, all_text: List[AnyStr], metadata: Dict[AnyStr, Any], tokens: List[str], token_offsets):
    print(f"{base_name}:")

    file_name = f"{base_name}.txt"
    print(f"exporting text to {file_name}")
    with open(file_name, 'w', encoding='utf-8') as f:
        f.writelines(all_text)

    file_name = f"{base_name}-tokens.json"
    print(f"exporting tokens to {file_name}")
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(tokens, f, indent=2)

    file_name = f"{base_name}-CoNLL_2002.txt"
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


def process_directory_group(group_name: str, directory_group: str):
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
    metadata = {"annotations": all_annotations}
    export(base_name, all_pars, metadata, tokens, token_offsets)


def init_spacy():
    global nlp
    nlp = spacy.load("nl_core_news_lg")


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
        init_spacy()
        directories = args.directory
        groups = itertools.groupby(directories, lambda d: d.rstrip('/').split('/')[-1].split('_')[0])
        for key, group in groups:
            process_directory_group(key, group)


if __name__ == '__main__':
    main()
