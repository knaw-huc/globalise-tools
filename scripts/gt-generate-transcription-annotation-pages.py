#!/usr/bin/env python3
import argparse
import json
import os
import sys
from argparse import Namespace
from pathlib import Path
from typing import Optional

from loguru import logger

import globalise_tools.pagexml_tools as pt
import globalise_tools.url_factory as uf

THIS_SCRIPT_PATH = "scripts/" + os.path.basename(__file__)


def get_arguments() -> Namespace:
    parser = argparse.ArgumentParser(
        description="Generate transcription AnnotationPage from the given pagexml",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-v",
                        help="Turn on logging",
                        action="store_true",
                        default=False,
                        dest='verbose'
                        )
    parser.add_argument("-p", "--pagexml",
                        help="The pagexml file",
                        type=str
                        )
    parser.add_argument("-t", "--pagetext",
                        help="The (post-processed) plain text of the pagexml",
                        type=str
                        )
    # parser.add_argument("-m",
    #                     "--manifests-dir",
    #                     help="The directory containing the manifest files, one per inventory number",
    #                     type=str,
    #                     required=True
    #                     )
    parser.add_argument("-o", "--output-dir",
                        help="The directory to write the annotation pages to",
                        type=str
                        )
    parser.add_argument("--git-commit",
                        help="The git commit to use for the provenance (will be calculated if omitted)",
                        type=str
                        )

    return parser.parse_args()


# def load_manifest(manifests_dir: str, inv_nr: str) -> dict[str, object]:
#     manifest_path = f"{manifests_dir}/{inv_nr}.json"
#     logger.info(f"<= {manifest_path}")
#     with open(manifest_path) as f:
#         manifest = json.load(f)
#     return manifest


def generate_transcription_annotation_page(out_dir: str, pagexml_path: str, page_text_path: str,
                                           commit_id: Optional[str] = None) -> None:
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
    # inv_nr = page_id.split("_")[-2]
    # page_no = int(page_id.split("_")[-1])
    canvas_id = uf.canvas_url(page_id)

    annotation_page = pt.convert_pagexml_to_web_annotations(
        xml_string=xml_string,
        canvas_id=canvas_id,
        page_text=page_text,
        script_path=THIS_SCRIPT_PATH,
        commit_id=commit_id
    )

    out_path = f"{out_dir}/{page_id}.json"
    logger.info(f"=> {out_path}")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(annotation_page, f, indent=2, ensure_ascii=False)


@logger.catch
def main() -> None:
    args = get_arguments()
    if not args.verbose:
        logger.remove()
        logger.add(sink=sys.stderr, level="WARNING")

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    generate_transcription_annotation_page(args.output_dir, args.pagexml, args.pagetext, args.git_commit)


if __name__ == '__main__':
    # # Creating profile object
    # ob = cProfile.Profile()
    # ob.enable()

    main()

    # ob.disable()
    # sec = io.StringIO()
    # sortby = SortKey.CUMULATIVE
    # ps = pstats.Stats(ob, stream=sec).sort_stats(sortby)
    # ps.print_stats()
    #
    # print(sec.getvalue())
