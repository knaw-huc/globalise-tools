#!/usr/bin/env python3
import argparse
import json
import sys
from argparse import Namespace
from pathlib import Path

import pagexml.parser as px
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


def page_annotation() -> dict[str, object]:
    return {
        "type": "Annotation",
        "id": "https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/annotations:transcriptions:NL-HaNA_1.04.02_3598_0797#page",
        "motivation": "supplementing",
        "textGranularity": "page",
        "body": [
            {
                "type": "TextualBody",
                "value": "A„o 1780\n„ „ 7 _„o „\nNotitie van Alle soo van, als na Batavia\n„en afgaande\nalhier ten Handel Komende, Vaertuij„\n„gen, te Weeten 't Ledert Primo October\nAnno Passato tot ultimo deeses Namentlijk\nAankomende Vaartuijgen\nden 3 october van Batavia den burger alhier Axel Anthonij Rosenquest\nper Paduwackang genaamt de Jonge Dirk\ngroot 20 lasten bemant met 30 koppen, was ge„\n„montheerd met 7 p„s metaele stukjes, 12 snap„\n„hanen 4 donderbussen „ rassegaaijen, 2 p. s pistoo„\n„len, 80 p„s Loode koegels en 40 lb bus kruijt, als\npassagiers den meede burger sebastiaan\nKnitel en den Jnlandsche vrouw Clara met\nhaar zoontje, brengt aan 10 vatjes booter 70 va„\n„tens bier 12 kassen wijn en bier en 5 kelders\ngenever\n_„o„ den Chinees Tiohaijsoe per dito van den oud Adsis„\n„tent Hendrik Bewers, groot 8 lasten, bemaant\nmet 24 koppen „ was gemontheerd met 6 p„s rantac„\n„kangs, 12 p„s snaphaenen, 6: p„s donderbussen, 25 p„s rond„\n„scherp, en 60 lb bus kruijt, als passagiers den meede\nChinees Theoenko, en den boegineesen Batjo en\nBasso brengt aan 1 kist amphioen 11 pijpen araa„\nen 10 Kassen aracq, 20 pic„s Randij suijker, 6 pi C:o oud\nKooper\n„\n"
            }
        ]
    }


def text_region_annotation() -> dict[str, object]:
    return {
        "type": "Annotation",
        "id": "https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/annotations:transcriptions:NL-HaNA_1.04.02_3598_0797#region_0751e75b-539e-4218-aae1-31099ed04177_6",
        "motivation": "highlighting",
        "textGranularity": "block",
        "body": [
            {
                "type": "SpecificResource",
                "source": {
                    "id": "https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/thesaurus:annotation:page-number",
                    "type": "skos:Concept",
                    "label": "page-number"
                },
                "purpose": "classifying"
            }
        ],
        "target": [
            {
                "type": "SpecificResource",
                "source": "https://data.globalise.huygens.knaw.nl/manifests/inventories/3598.json/canvas/p797",
                "selector": {
                    "type": "SvgSelector",
                    "value": "<path d=\"M3207,334 3207,337 3203,341 3203,345 3199,349 3199,353 3195,357 3195,372 3199,372 3203,376 3215,376 3218,380 3245,380 3249,376 3261,376 3268,368 3268,345 3264,341 3264,337 3257,330 3245,330 3241,326 3218,326 3215,330 3211,330z\"/>"
                }
            },
            {
                "id": "https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/annotations:transcriptions:NL-HaNA_1.04.02_3598_0797#page",
                "type": "Annotation"
            }
        ]
    }


def word_annotation() -> dict[str, object]:
    return {
        "type": "Annotation",
        "id": "https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/annotations:transcriptions:NL-HaNA_1.04.02_3598_0797#word_cbb27ee2-86f2-4643-8b75-1d929a62e80b",
        "motivation": "supplementing",
        "textGranularity": "word",
        "body": [
            {
                "type": "TextualBody",
                "value": "A„o"
            }
        ],
        "target": [
            {
                "type": "SpecificResource",
                "source": "https://data.globalise.huygens.knaw.nl/manifests/inventories/3598.json/canvas/p797",
                "selector": {
                    "type": "SvgSelector",
                    "value": "<path d=\"M247,1799 297,1798 346,1795 376,1794 376,1839 349,1840 298,1843 248,1844z\"/>"
                }
            },
            {
                "id": "https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/annotations:transcriptions:NL-HaNA_1.04.02_3598_0797#e0d3a9c5-05ec-4d22-a93f-c4324836db9c",
                "type": "Annotation"
            }
        ]
    }


def line_annotation() -> dict[str, object]:
    return {
        "type": "Annotation",
        "id": "https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/annotations:transcriptions:NL-HaNA_1.04.02_3598_0797#e0d3a9c5-05ec-4d22-a93f-c4324836db9c",
        "motivation": "supplementing",
        "textGranularity": "line",
        "body": [
            {
                "type": "TextualBody",
                "value": "A„o 1780"
            }
        ],
        "target": [
            {
                "type": "SpecificResource",
                "source": "https://data.globalise.huygens.knaw.nl/manifests/inventories/3598.json/canvas/p797",
                "selector": {
                    "type": "SvgSelector",
                    "value": "<path d=\"M195,1705 384,1704 433,1749 642,1739 639,1850 394,1838 289,1850 195,1849z\"/>"
                }
            },
            {
                "id": "https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/annotations:transcriptions:NL-HaNA_1.04.02_3598_0797#region_d106dbbd-218f-4075-80f8-bfe69352d0b6_11",
                "type": "Annotation"
            }
        ]
    }


def generate_transcription_annotation_page(out_dir: str, page_xml_path: str) -> None:
    page_id = page_xml_path.split("/")[-1].replace(".xml", "")
    inv_nr = page_id.split("_")[-2]
    page_no = page_id.split("_")[-1]
    manifest = load_manifest(inv_nr)
    canvas_dimensions = [[c["width"], c["height"]] for c in manifest["items"]]
    width, height = canvas_dimensions[int(page_no) - 1]

    items = []
    scan_doc = px.parse_pagexml_file(pagexml_file=page_xml_path)
    scan_doc.get_regions()

    annotation_page = {
        "@context": [
            "http://iiif.io/api/extension/text-granularity/context.json",
            "http://iiif.io/api/presentation/3/context.json"
        ],
        "type": "AnnotationPage",
        "id": f"https://globalise-huygens.github.io/document-view-sandbox/iiif/annotations/transcriptions/{page_id}.json",
        "label": f"Transcription of {page_id}.jpg",
        "partOf": {
            "id": f"https://data.globalise.huygens.knaw.nl/manifests/inventories/{inv_nr}.json/canvas/p{page_no}",
            "type": "Canvas",
            "width": width,
            "height": height,
        },
        "items": []
    }
    out_path = f"{out_dir}/{page_id}.json"
    logger.info(f"=> {out_path}")
    with open(out_path, 'w') as f:
        json.dump(obj=annotation_page, fp=f)


def generate_transcription_annotation_page1(out_dir: str, pagexml_path: str, page_text_path: str) -> None:
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
    generate_transcription_annotation_page1(args.output_dir, args.pagexml, args.pagetext)


if __name__ == '__main__':
    main()
