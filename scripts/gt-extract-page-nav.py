#!/usr/bin/env python3
import glob
import json
from typing import List, Dict

import progressbar
from loguru import logger


@logger.catch
def main() -> None:
    widgets = [
        '[',
        progressbar.SimpleProgress(),
        progressbar.Bar(marker='\x1b[32m#\x1b[39m'),
        progressbar.Timer(),
        '|',
        progressbar.ETA(),
        ']'
    ]
    paths = manifest_paths("/Users/bram/e/globalise/manifests/inventories")
    with progressbar.ProgressBar(widgets=widgets, max_value=len(paths), redirect_stdout=True) as bar:
        for i, path in enumerate(paths):
            process_manifest(path)
            bar.update(i)


def manifest_paths(directory: str) -> List[str]:
    return glob.glob(f"{directory}/*.json")


def generate_prev_next_map(pagexml_ids: List[str]) -> Dict[str, Dict[str, str]]:
    prev_next_idx = {}
    last_idx = len(pagexml_ids) - 1
    for i, pid in enumerate(pagexml_ids):
        nav = {}
        if i > 0:
            nav['prev'] = pagexml_ids[i - 1]
        if i < last_idx:
            nav['next'] = pagexml_ids[i + 1]
        prev_next_idx[pid] = nav
    return prev_next_idx


def process_manifest(path):
    # logger.info(f"<= {path}")
    with open(path) as f:
        manifest = json.load(f)
    inv_nr = path.split('/')[-1].replace('.json', '')
    pagexml_ids = [i["label"]['en'][0] for i in manifest['items']]
    nav_idx = generate_prev_next_map(pagexml_ids)

    path = f"out/page_nav_idx_{inv_nr}.json"
    # logger.info(f"=> {path}")
    with open(path, 'w') as f:
        json.dump(nav_idx, fp=f, indent=4)


if __name__ == '__main__':
    main()
