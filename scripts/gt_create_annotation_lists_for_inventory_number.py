#!/usr/bin/env python3
import argparse
import copy
import os
import sys
import time
from argparse import Namespace
from pathlib import Path
from typing import Any

import orjson
from loguru import logger

import globalise_tools.io_tools as rw
import globalise_tools.url_factory as uf
import scripts.gt_ner_xmi_to_wa as nx
from globalise_tools.annotation_page_factory import AnnotationPageFactory
from globalise_tools.events import EVENT_TO_CATEGORY, CATEGORY_TO_LABEL
from globalise_tools.logger_tools import log_writing_file
from globalise_tools.url_factory import AnnotationPageType

# adjust if this file is moved
THIS_SCRIPT_PATH = "scripts/" + os.path.basename(__file__)


def get_arguments() -> Namespace:
    parser = argparse.ArgumentParser(
        description="Generate entity, event and transcription annotation pages for the given inventory number",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-v",
                        help="Turn on logging",
                        action="store_true",
                        dest='verbose'
                        )
    parser.add_argument("-p", "--pagexml-dir",
                        help="The directory containing the pagexml files",
                        required=True,
                        type=Path
                        )
    parser.add_argument("-x", "--xmi-dir",
                        help="The directory containing the xmi files",
                        required=True,
                        type=Path
                        )
    parser.add_argument("-o", "--output-dir",
                        help="The directory to write the annotation pages to",
                        required=True,
                        type=Path
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
                        type=Path,
                        required=True
                        )
    parser.add_argument("-e",
                        "--event-mapping",
                        help="The path to the eventmapping.json to use",
                        type=Path,
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


def _with_nested_classification(event_name: str, event_spec: dict[str, Any]) -> dict[str, Any]:
    new_event_spec = copy.deepcopy(event_spec)
    # event_mapping contains event types that are no longer used in the xmi, and aren't featured in EVENT_TO_CATEGORY
    # leave them as-is
    if event_name in EVENT_TO_CATEGORY:
        category_id = EVENT_TO_CATEGORY[event_name]
        nested_classification = {
            "id": category_id,
            "type": "Type",
            "_label": CATEGORY_TO_LABEL[category_id]
        }
        new_event_spec["classified_as"]["id"] = uf.event_url(event_name)
        new_event_spec["classified_as"]["classified_as"] = nested_classification
    return new_event_spec


def _add_classified(event_mapping_in: dict[str, Any]) -> dict[str, Any]:
    return {k: _with_nested_classification(k, v) for (k, v) in event_mapping_in.items()}


@logger.catch()
def main():
    tic = time.perf_counter()

    args = get_arguments()
    if not args.verbose:
        logger.remove()
        logger.add(sink=sys.stderr, level="WARNING")

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    timespan4inventory = nx.load_timespan_dict()
    raw_event_mapping = rw.read_json(args.event_mapping)
    event_mapping = _add_classified(raw_event_mapping)
    xpf = nx.XMIProcessorFactory(args.type_system, timespan4inventory, event_mapping, args.git_commit)

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
    store_annotation_pages(pages_dict=apf.transcription_pages, output_dir=args.output_dir,
                           page_type=AnnotationPageType.TRANSCRIPTIONS)
    store_annotation_pages(pages_dict=apf.entity_pages, output_dir=args.output_dir,
                           page_type=AnnotationPageType.ENTITIES)
    store_annotation_pages(pages_dict=apf.event_pages, output_dir=args.output_dir, page_type=AnnotationPageType.EVENTS)

    toc = time.perf_counter()
    print(
        f"created {len(apf.transcription_pages) + len(apf.entity_pages) + len(apf.event_pages)} annotation pages in {toc - tic:0.4f} seconds")

    errors = xpf.errors + apf.errors
    if errors:
        print(f"{len(errors)} errors occurred:")
        for error in errors:
            print(f"  {error}")
        sys.exit(1)


def store_annotation_pages(
        pages_dict: dict[str, dict[str, Any]],
        output_dir: str,
        page_type: AnnotationPageType
) -> None:
    os.makedirs(f"{output_dir}/{page_type.value}", exist_ok=True)
    for (page_id, page) in pages_dict.items():
        page_path = f"{output_dir}/{page_type.value}/{page_id}.json"
        log_writing_file(page_path)
        with open(page_path, "wb") as f:
            f.write(orjson.dumps(page))


if __name__ == '__main__':
    main()
