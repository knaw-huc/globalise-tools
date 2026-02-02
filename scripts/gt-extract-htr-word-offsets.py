#!/usr/bin/env python3
import argparse
import json
import sys
from argparse import Namespace
from pathlib import Path

from loguru import logger

from globalise_tools.model import AnnotationEncoder
from globalise_tools.pagexml_tools import TranscriptionAnnotationPageBuilder


def get_arguments() -> Namespace:
    parser = argparse.ArgumentParser(
        description="Extract word offsets from the given pagexml",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-v",
                        help="Turn on logging",
                        action="store_true",
                        default=False,
                        dest='verbose'
                        )
    parser.add_argument("-o", "--output-dir",
                        help="The directory to write the offset files to",
                        default="/tmp",
                        type=str
                        )
    parser.add_argument("pagexml_paths",
                        help="The pagexml file(s)",
                        type=str,
                        nargs="+",
                        )
    return parser.parse_args()


def extract_word_offsets(out_dir: str, pagexml_paths: list[str]):
    for pagexml_path in pagexml_paths:
        try:
            logger.info(f"<= {pagexml_path}")
            with open(pagexml_path, "r", encoding="utf-8") as f:
                xml_string = f.read()
        except FileNotFoundError:
            print(f"Input file not found: {pagexml_path}", file=sys.stderr)
            sys.exit(1)

        page_id = pagexml_path.split("/")[-1].replace(".xml", "")

        htr_word_offsets = TranscriptionAnnotationPageBuilder(xml_string=xml_string).htr_word_offsets

        out_path = f"{out_dir}/{page_id}.json"
        logger.info(f"=> {out_path}")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(htr_word_offsets, f, indent=2, ensure_ascii=False, cls=AnnotationEncoder)


@logger.catch
def main():
    args = get_arguments()
    if not args.verbose:
        logger.remove()
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    extract_word_offsets(args.output_dir, args.pagexml_paths)


if __name__ == '__main__':
    main()
