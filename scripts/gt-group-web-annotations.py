#!/usr/bin/env python3
import glob
import json
import sys
from collections import defaultdict
from itertools import groupby
from typing import List

import progressbar
from loguru import logger


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
    with progressbar.ProgressBar(widgets=widgets, max_value=len(paths), redirect_stdout=True) as bar:
        for i, file_path in enumerate(paths):
            grouped = group_annotations(file_path)
            for body_type, annotations in grouped:
                grouped_annotations[body_type].extend(annotations)
            bar.update(i)
    for body_type in grouped_annotations.keys():
        annotations = grouped_annotations[body_type]
        out_path = f"{root_path}/{body_type.lower().replace(':', '_')}_annotations.json"
        print(f"writing {len(annotations)} {body_type} annotations to {out_path}")
        with open(out_path, 'w') as f:
            json.dump(annotations, fp=f)


def annotations_paths(apath: str) -> List[str]:
    return glob.glob(f"{apath}/*.json")


def group_annotations(json_path):
    # inv_nr = path.split('/')[-1].replace('.json', '')
    # logger.info(f"<= {path}")
    with open(json_path) as f:
        annotations = json.load(f)
    return groupby(annotations, key=lambda a: a['body']['type'])


if __name__ == '__main__':
    path = sys.argv[1]
    main(path)
