#!/usr/bin/env python3
import argparse
import json
import sys
from argparse import Namespace
from pathlib import Path

from loguru import logger

from globalise_tools.pagexml_tools import convert_pagexml_to_web_annotations


def get_arguments() -> Namespace:
    parser = argparse.ArgumentParser(
        description="Generate transcription AnnotationPage from the given pagexml",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-p", "--pagexml",
                        help="The pagexml file",
                        type=str
                        )
    parser.add_argument("-t", "--pagetext",
                        help="The (post-processed) plain text of the pagexml",
                        type=str
                        )
    parser.add_argument("-o", "--output-dir",
                        help="The directory to write the annotation pages to",
                        type=str
                        )
    return parser.parse_args()


def load_manifest(inv_nr: str) -> dict[str, object]:
    manifest_path = f"/Users/bram/workspaces/globalise/manifests/inventories/{inv_nr}.json"
    logger.info(f"<= {manifest_path}")
    with open(manifest_path) as f:
        manifest = json.load(f)
    return manifest


# def generate_transcription_annotation_page0(out_dir: str, page_xml_path: str) -> None:
#     page_id = page_xml_path.split("/")[-1].replace(".xml", "")
#     inv_nr = page_id.split("_")[-2]
#     page_no = page_id.split("_")[-1]
#     manifest = load_manifest(inv_nr)
#     canvas_dimensions = [[c["width"], c["height"]] for c in manifest["items"]]
#     width, height = canvas_dimensions[int(page_no) - 1]
#
#     items = []
#     scan_doc = px.parse_pagexml_file(pagexml_file=page_xml_path)
#     scan_doc.get_regions()
#
#     annotation_page = {
#         "@context": [
#             "http://iiif.io/api/extension/text-granularity/context.json",
#             "http://iiif.io/api/presentation/3/context.json",
#             "http://www.w3.org/ns/anno.jsonld",
#             {
#                 "transcription-diplomatic": {
#                     "@id": "https://digitaalerfgoed.poolparty.biz/globalise/annotation/transcription/transcription-diplomatic"
#                 },
#                 "transcription-normalized": {
#                     "@id": "https://digitaalerfgoed.poolparty.biz/globalise/annotation/transcription/transcription-normalized"
#                 }
#             }
#         ],
#         "type": "AnnotationPage",
#         "id": f"https://globalise-huygens.github.io/document-view-sandbox/iiif/annotations/transcriptions/{page_id}.json",
#         "label": f"Transcription of {page_id}.jpg",
#         "partOf": {
#             "id": f"https://data.globalise.huygens.knaw.nl/manifests/inventories/{inv_nr}.json/canvas/p{page_no}",
#             "type": "Canvas",
#             "width": width,
#             "height": height,
#         },
#         "items": []
#     }
#     out_path = f"{out_dir}/{page_id}.json"
#     logger.info(f"=> {out_path}")
#     with open(out_path, 'w') as f:
#         json.dump(obj=annotation_page, fp=f)


def generate_transcription_annotation_page(out_dir: str, pagexml_path: str, page_text_path: str) -> None:
    try:
        logger.info(f"<= {pagexml_path}")
        with open(pagexml_path, "r", encoding="utf-8") as f:
            xml_string = f.read()
    except FileNotFoundError:
        print(f"Input file not found: {pagexml_path}", file=sys.stderr)
        sys.exit(1)

    try:
        logger.info(f"<= {page_text_path}")
        with open(page_text_path, "r", encoding="utf-8") as f:
            page_text = f.read()
    except FileNotFoundError:
        print(f"Input file not found: {page_text_path}", file=sys.stderr)
        sys.exit(1)

    page_id = pagexml_path.split("/")[-1].replace(".xml", "")
    inv_nr = page_id.split("_")[-2]
    page_no = int(page_id.split("_")[-1])
    canvas_id = f"https://data.globalise.huygens.knaw.nl/manifests/inventories/{inv_nr}.json/canvas/p{page_no}"

    annotation_page = convert_pagexml_to_web_annotations(xml_string, canvas_id, page_text)

    out_path = f"{out_dir}/{page_id}.json"
    logger.info(f"=> {out_path}")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(annotation_page, f, indent=2, ensure_ascii=False)


@logger.catch
def main():
    args = get_arguments()
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    generate_transcription_annotation_page(args.output_dir, args.pagexml, args.pagetext)


if __name__ == '__main__':
    main()
