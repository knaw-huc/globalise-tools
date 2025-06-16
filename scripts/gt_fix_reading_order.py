#!/usr/bin/env python3
import argparse
import os.path

from loguru import logger

import globalise_tools.document_metadata as DM
from globalise_tools.document_metadata import DocumentMetadata
from globalise_tools.page_xml_fixer import PageXmlFixer

fixable_error_codes = ['3.1.1', '3.1.2', '3.2']


@logger.catch
def get_arguments():
    parser = argparse.ArgumentParser(
        description="Read the given PageXML files and fix the reading order when required."
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
    parser.add_argument("-m",
                        "--document-metadata-path",
                        required=True,
                        help="The path(s) to the document_metadata.csv file(s) containing the document definitions.",
                        nargs="+",
                        type=str)
    # parser.add_argument("pagexml_path",
    #                     help="The path to the pagexml file",
    #                     nargs="*",
    #                     type=str)
    return parser.parse_args()


@logger.catch
def fix_reading_order(input_directory: str, output_directory: str, document_metadata_paths: list[str]):
    relevant_documents = [r for r in DM.read_document_selection(document_metadata_paths) if is_relevant(r)]
    pagexml_paths = []
    quality_check = {}
    for dm in relevant_documents:
        pagexml_dir = f"{input_directory}/{dm.inventory_number}"
        for pid in dm.pagexml_ids:
            pagexml_path = f"{pagexml_dir}/{pid}.xml"
            pagexml_paths.append(pagexml_path)
            quality_check[pagexml_path] = dm.quality_check
    total = len(pagexml_paths)
    for i, import_path in enumerate(pagexml_paths):
        logger.info(f"<= {import_path} ({i + 1}/{total})")
        if os.path.exists(import_path):
            PageXmlFixer(import_path, output_directory, quality_check[import_path]).fix()
        else:
            logger.warning(f"missing file: {import_path}")


def is_relevant(document_metadata: DocumentMetadata) -> bool:
    quality_check = document_metadata.quality_check
    return '3.1.1' in quality_check or '3.1.2' in quality_check or '3.2' in quality_check and document_metadata.scan_range != ""


# def has_problematic_text_region_reading_order(pd: pdm.PageXMLDoc) -> bool:
#     paragraphs = [tr for tr in pd.get_text_regions_in_reading_order() if 'paragraph' in defining_types(tr)]
#     if len(paragraphs) > 1:
#         if is_portrait(pd):
#             y_values = [p.coords.box['y'] for p in paragraphs]
#             sorted_y_values = sorted(y_values)
#             is_problematic = y_values != sorted_y_values
#             if is_problematic:
#                 # print("problematic paragraph reading order because of y_value order")
#                 return is_problematic
#         else:
#             # assume 2 pages
#             middle_x = pd.coords.box['w'] / 2
#             left_paragraphs = [tr for tr in paragraphs if tr.coords.box['x'] < middle_x]
#             right_paragraphs = [tr for tr in paragraphs if tr.coords.box['x'] >= middle_x]
#             if len(left_paragraphs) > 1:
#                 y_values = [p.coords.box['y'] for p in left_paragraphs]
#                 sorted_y_values = sorted(y_values)
#                 if y_values != sorted_y_values:
#                     # print("problematic paragraph reading order because of y_value order in left page")
#                     return True
#             if len(right_paragraphs) > 1:
#                 y_values = [p.coords.box['y'] for p in right_paragraphs]
#                 sorted_y_values = sorted(y_values)
#                 if y_values != sorted_y_values:
#                     # print("problematic paragraph reading order because of y_value order in right page")
#                     return True
#             return False
#     else:
#         return False

def main():
    args = get_arguments()
    if args.document_metadata_path:
        fix_reading_order(args.input_directory, args.output_directory, args.document_metadata_path)


if __name__ == '__main__':
    main()
