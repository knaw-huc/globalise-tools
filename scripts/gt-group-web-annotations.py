#!/usr/bin/env python3
import glob
import json
import sys
from collections import defaultdict
from itertools import groupby

import progressbar
from loguru import logger

from globalise_tools.nav_provider import NavProvider


@logger.catch
def main(root_path) -> None:
    widgets = [
        '[',
        progressbar.SimpleProgress(),
        progressbar.Bar(marker='\x1b[32m#\x1b[39m'),
        progressbar.Timer(),
        '|',
        progressbar.ETA(),
        ']'
    ]
    paths = annotations_paths(path)
    grouped_annotations = defaultdict(list)
    nav_provider = NavProvider()
    with progressbar.ProgressBar(widgets=widgets, max_value=len(paths), redirect_stdout=True) as bar:
        for i, file_path in enumerate(paths):
            grouped = group_annotations(file_path)
            for body_type, annotations in grouped:
                grouped_annotations[body_type].extend(post_process(annotations, body_type, nav_provider))
            bar.update(i)
    for body_type in grouped_annotations.keys():
        annotations = grouped_annotations[body_type]
        out_path = f"{root_path}/{body_type.lower().replace(':', '_')}_annotations.json"
        print(f"writing {len(annotations)} {body_type} annotations to {out_path}")
        with open(out_path, 'w') as f:
            json.dump(annotations, fp=f)


def annotations_paths(apath: str) -> list[str]:
    return glob.glob(f"{apath}/NL*.json")


def get_inv_nr(file_path: str):
    file = file_path.split('/')[-1]
    return file.split('_')[-3]


RELEVANT_BODY_TYPES = {"na:File", "px:Page"}


def group_annotations(json_path):
    # inv_nr = path.split('/')[-1].replace('.json', '')
    # logger.info(f"<= {path}")
    with open(json_path) as f:
        annotations = json.load(f)
    filtered_annotations = [a for a in annotations if a['body']['type'] in RELEVANT_BODY_TYPES]
    return groupby(filtered_annotations, key=lambda a: a['body']['type'])


def post_process(annotations: list[dict[str, any]], body_type: str, nav_provider: NavProvider) -> list[dict[str, any]]:
    return [post_processed(a, body_type, nav_provider) for a in annotations]


def post_processed(annotation: dict[str, any], body_type: str, nav_provider: NavProvider) -> dict[str, any]:
    if body_type == "na:File":
        meta_value = annotation['body']['metadata'].pop('file')
        annotation['body']['metadata']['na:File'] = meta_value
    if body_type == "px:Page":
        meta_value = annotation['body']['metadata']['document']
        page_id = ".".join(meta_value.split('.')[:-1])
        annotation['body']['metadata']['document'] = page_id
        annotation['body']['metadata'].update(nav_provider.nav_fields(page_id))
    return annotation


if __name__ == '__main__':
    path = sys.argv[1]
    main(path)
