#!/usr/bin/env python3
import argparse
import os
import sys
import time
from argparse import Namespace
from pathlib import Path
from typing import Any

import orjson
from loguru import logger

import scripts.gt_ner_xmi_to_wa as nx
from globalise_tools.annotation_page_factory import AnnotationPageFactory
from globalise_tools.url_factory import AnnotationPageType

THIS_SCRIPT_PATH = "scripts/" + os.path.basename(__file__)


def get_arguments() -> Namespace:
    parser = argparse.ArgumentParser(
        description="Generate entity and transcription annotation pages for the given inventory number",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-v",
                        help="Turn on logging",
                        action="store_true",
                        default=False,
                        dest='verbose'
                        )
    parser.add_argument("-p", "--pagexml-dir",
                        help="The directory containing the pagexml files",
                        required=True,
                        type=str
                        )
    parser.add_argument("-x", "--xmi-dir",
                        help="The directory containing the xmi files",
                        required=True,
                        type=str
                        )
    parser.add_argument("-o", "--output-dir",
                        help="The directory to write the annotation pages to",
                        required=True,
                        type=str
                        )
    parser.add_argument("-m",
                        "--manifest",
                        help="The path to the manifest file for the inventory number",
                        type=str,
                        required=True
                        )
    parser.add_argument("-t",
                        "--type-system",
                        help="The path to the TypeSystem.xml to use",
                        type=str,
                        required=True
                        )
    parser.add_argument("--git-commit",
                        help="The git commit to use for the provenance (will be calculated if omitted)",
                        type=str
                        )
    parser.add_argument("inventory_number",
                        help="The inventory number to process",
                        type=str,
                        )
    return parser.parse_args()


@logger.catch
def main():
    tic = time.perf_counter()

    args = get_arguments()
    if not args.verbose:
        logger.remove()
        logger.add(sink=sys.stderr, level="WARNING")

    for path in [args.pagexml_dir, args.xmi_dir, args.output_dir]:
        Path(path).mkdir(parents=True, exist_ok=True)

    timespan4inventory = nx.load_timespan_dict()
    xpf = nx.XMIProcessorFactory(args.type_system, timespan4inventory, args.git_commit)

    logger.info(f"processing inventory number {args.inventory_number}")
    apf = AnnotationPageFactory(
        inventory_number=args.inventory_number,
        pagexml_dir=args.pagexml_dir,
        xmi_dir=args.xmi_dir,
        xmi_processor_factory=xpf,
        manifest_path=args.manifest,
        script_path=THIS_SCRIPT_PATH
    )
    apf.build_annotation_pages()
    store_annotation_pages(apf.transcription_pages, args.output_dir, AnnotationPageType.TRANSCRIPTIONS)
    store_annotation_pages(apf.entity_pages, args.output_dir, AnnotationPageType.ENTITIES)

    toc = time.perf_counter()
    print(
        f"created {len(apf.transcription_pages) + len(apf.entity_pages)} annotation pages in  {toc - tic:0.4f} seconds")

    errors = xpf.errors + apf.errors
    if errors:
        print(f"{len(errors)} errors occurred:")
        for error in errors:
            print(f"  {error}")
        exit(1)


def store_annotation_pages(pages_dict: dict[str, dict[str, Any]], output_dir: str, type: AnnotationPageType) -> None:
    for (page_id, page) in pages_dict.items():
        os.makedirs(f"{output_dir}/{type.value}", exist_ok=True)
        page_path = f"{output_dir}/{type.value}/{page_id}.json"
        logger.info(f"=> {page_path}")
        with open(page_path, "wb") as f:
            f.write(orjson.dumps(page))


if __name__ == '__main__':
    main()
