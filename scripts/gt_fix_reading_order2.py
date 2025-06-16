#!/usr/bin/env python3
import argparse
import os.path

from loguru import logger

import globalise_tools.document_metadata as DM
from globalise_tools.document_metadata import DocumentMetadata
from globalise_tools.page_xml_fixer import PageXmlFixer


@logger.catch
def get_arguments():
    parser = argparse.ArgumentParser(
        description="Read the PageXML files from the given folders and fix the reading order when required."
                    " When the reading order is fixed, write the PageXML with the modified reading order"
                    " to the given export directory",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i",
                        "--input-directory",
                        required=True,
                        help="The directory where the original PageXML files are stored, grouped by inventory number.",
                        type=str)
    parser.add_argument("-o",
                        "--output-directory",
                        required=True,
                        help="The directory to store the modified PageXML files in.",
                        type=str)
    return parser.parse_args()


@logger.catch
def fix_reading_order(input_directory: str, output_directory: str, inventory_numbers: list[str]):
    pagexml_paths = []
    quality_check = {}
    for inv in inventory_numbers:
        pagexml_dir = f"{input_directory}/{inv}"
        pagexml_paths = list_pagexml_files(pagexml_dir)
    total = len(pagexml_paths)
    for i, import_path in enumerate(pagexml_paths):
        logger.info(f"<= {import_path} ({i + 1}/{total})")
        if os.path.exists(import_path):
            PageXmlFixer(
                import_path,
                output_directory,
                [],
                "gt_fix_reading_order2.py"
            ).fix()
        else:
            logger.warning(f"missing file: {import_path}")


def list_pagexml_files(directory: str):
    all_files = os.listdir(directory)
    return sorted([f'{directory}/{f}' for f in all_files if f.endswith(".xml")])


def main():
    args = get_arguments()
    if args.input_directory:
        fix_reading_order(args.input_directory, args.output_directory, ["9999"])


if __name__ == '__main__':
    main()
