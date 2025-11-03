#!/usr/bin/env python3
import argparse
import json
from itertools import groupby

from loguru import logger


def get_arguments():
    parser = argparse.ArgumentParser(
        description="Group web-annotations to an AnnotationPage, per page",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("annotations",
                        help="The file containing the annotations",
                        type=str
                        )
    return parser.parse_args()


def as_item(a: dict[str, object]) -> dict[str, object]:
    a.pop("@context")
    return a


def write_annotation_page(out_dir: str, pageid: str, page_annotations: list[dict[str, object]]):
    inv_nr = pageid.split("_")[-2]
    page_no = pageid.split("_")[-1]
    context = ["http://iiif.io/api/presentation/3/context.json"]
    annotation_context = page_annotations[0]["@context"]  # assumption: all annotations have the same @context
    context += annotation_context
    items = [as_item(a) for a in page_annotations]
    page = {
        "@context": context,
        "type": "AnnotationPage",
        "id": f"https://globalise-huygens.github.io/document-view-sandbox/iiif/annotations/transcriptions/{pageid}.json",
        "label": f"Entities of {pageid}.jpg",
        "partOf": {
            "id": f"https://data.globalise.huygens.knaw.nl/manifests/inventories/{inv_nr}.json/canvas/p{page_no}",
            "type": "Canvas",
            # "height": 5469,
            # "width": 3928
        },
        "items": items
    }
    out_path = f"{out_dir}/annotation-page_{pageid}.json"
    logger.info(f"=> {out_path}")
    with open(out_path, "w") as f:
        json.dump(page, f)


def page_id(annotation: dict[str, object]) -> str:
    # ic(annotation)
    target_id = annotation["target"][0]["source"]["id"]
    return target_id.replace("https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/annotations:transcriptions:",
                             "").replace("#page", "")


def group_to_page(annotations_path: str):
    logger.info(f"<= {annotations_path}")
    out_dir = "/".join(annotations_path.split("/")[:-1])

    with open(annotations_path) as f:
        annotations = json.load(f)

    groups = groupby(annotations, lambda x: page_id(x))
    for pgid, page_annotations in groups:
        write_annotation_page(out_dir, pgid, [pa for pa in page_annotations])


@logger.catch
def main():
    args = get_arguments()
    group_to_page(args.annotations)


if __name__ == '__main__':
    main()
