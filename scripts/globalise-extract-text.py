#!/usr/bin/env python3
import argparse
import os
from typing import List, AnyStr

from pagexml.parser import parse_pagexml_file


def list_pagexml_files(directory: str):
    all_files = os.listdir(directory)
    return sorted([f'{directory}/{f}' for f in all_files if f.endswith(".xml")])


def extract_paragraphs(path):
    scan_doc = parse_pagexml_file(path)
    lines = scan_doc.get_lines()
    return [line.text + "\n" for line in lines]


def export(base_name: AnyStr, all_text: List[AnyStr]):
    file_name = f"{base_name}.txt"
    with open(file_name, 'w') as f:
        f.writelines(all_text)


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
        all_text = []
        for f in pagexml_files:
            paragraphs = extract_paragraphs(f)
            all_text += paragraphs
        base_name = directory.split('/')[-1]
        export(base_name, all_text)


if __name__ == '__main__':
    main()
