#!/usr/bin/env python3
import glob
import json
import os

import progressbar
from loguru import logger

from globalise_tools.nav_provider import index_path_for_inv_nr


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


def manifest_paths(directory: str) -> list[str]:
    return glob.glob(f"{directory}/*.json")


def generate_prev_next_map(pagexml_ids: list[str]) -> dict[str, dict[str, str]]:
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

    path = index_path_for_inv_nr(inv_nr)
    dir_path = "/".join(path.split('/')[:-1])
    os.makedirs(dir_path, exist_ok=True)
    # logger.info(f"=> {path}")
    with open(path, 'w') as f:
        json.dump(nav_idx, fp=f, indent=4)


if __name__ == '__main__':
    main()
