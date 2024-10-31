#!/usr/bin/env python3
import glob
import json
import sys

import progressbar
from loguru import logger

chunk_size = 30000


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
    textline_annotations = []
    with progressbar.ProgressBar(widgets=widgets, max_value=len(paths), redirect_stdout=True) as bar:
        chunk_count = 0
        for i, file_path in enumerate(paths):
            textline_annotations.extend(filter_annotations(file_path))
            while len(textline_annotations) > chunk_size:
                chunk = textline_annotations[:chunk_size]
                chunk_count += 1
                rest = textline_annotations[chunk_size:]
                textline_annotations = rest
                store_chunk(chunk, root_path, chunk_count)
            bar.update(i)
        if textline_annotations:
            chunk_count += 1
            store_chunk(textline_annotations, root_path, chunk_count)


def annotations_paths(apath: str) -> list[str]:
    return glob.glob(f"{apath}/NL*.json")


def get_inv_nr(file_path: str):
    file = file_path.split('/')[-1]
    return file.split('_')[-3]


# RELEVANT_BODY_TYPES = {"na:File", "px:Page"}
RELEVANT_BODY_TYPES = {"px:TextLine"}


def filter_annotations(json_path):
    with open(json_path) as f:
        annotations = json.load(f)
    return [a for a in annotations if a['body']['type'] in RELEVANT_BODY_TYPES]


def store_chunk(annotations, root_path, chunk_count):
    fpath = f'{root_path}/px_textline_annotations_{chunk_count:04d}.json'
    print(f'=> {fpath}')
    with open(fpath, 'w') as f:
        json.dump(annotations, fp=f)


if __name__ == '__main__':
    path = sys.argv[1]
    main(path)
