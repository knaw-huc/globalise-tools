#!/usr/bin/env python3
import argparse

from loguru import logger

import globalise_tools.document_metadata as DM
from globalise_tools.document_metadata import DocumentMetadata


@logger.catch
def get_arguments():
    parser = argparse.ArgumentParser(
        description="List the PageXML file names of documents marked as needing a reading order correction in the given"
                    " document_metadata.csv\n"
                    "(currently those marked with 3.1.1, 3.1.2, and/or 3.2 in"
                    " the `Quality Check` column and a valid value in the `scan_range` column)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("document_metadata_path",
                        help="The path to the document_metadata.csv file containing the document definitions.",
                        type=str)
    return parser.parse_args()


@logger.catch
def list_relevant_pagexml_names(document_metadata_path: str):
    relevant_documents = [r for r in DM.read_document_metadata(document_metadata_path) if is_relevant(r)]
    for dm in relevant_documents:
        for pid in dm.pagexml_ids:
            print(pid)


def is_relevant(document_metadata: DocumentMetadata) -> bool:
    quality_check = document_metadata.quality_check
    return '3.1.1' in quality_check or '3.1.2' in quality_check or '3.2' in quality_check and document_metadata.scan_range != ""


if __name__ == '__main__':
    args = get_arguments()
    if args.document_metadata_path:
        list_relevant_pagexml_names(args.document_metadata_path)
