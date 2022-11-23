#!/usr/bin/env python3
import argparse
import csv
import os
from pathlib import Path

import requests
from tqdm import tqdm


def to_mets_id(url: str) -> str:
    return url.split('/')[-1]


def print_failed_urls(failed_urls):
    size = len(failed_urls)
    if size > 0:
        print(f"\n{size} failed mets urls:")
        for f in failed_urls:
            print(f)


def download_mets(data_dir: str):
    mets_csv = f'{data_dir}/NL-HaNA_1.04.02_mets.csv'
    print(f"reading {mets_csv}...")
    with open(mets_csv) as f:
        records = [r for r in csv.DictReader(f) if r['METS link'] != '']

    bar = tqdm(range(len(records)))
    failed_urls = []

    os.makedirs(os.path.join(data_dir, "mets"), exist_ok=True)

    for i in bar:
        url = records[i]['METS link']
        mets_id = to_mets_id(url)
        path = f'{data_dir}/mets/{mets_id}.xml'
        if not Path(path).is_file():
            bar.set_description(f"reading {url}...")
            r = requests.get(url)
            if r.ok:
                xml = r.text
                path = f'{data_dir}/mets/{mets_id}.xml'
                with open(path, 'w') as f:
                    bar.set_description(f"writing to {path}...")
                    f.write(xml)
            else:
                failed_urls.append(url)

    print_failed_urls(failed_urls)


def get_arguments():
    parser = argparse.ArgumentParser(
        description="Download METS files",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-d",
                        "--data-dir",
                        required=True,
                        help="The data directory.",
                        type=str,
                        metavar="data_dir")
    return parser.parse_args()


if __name__ == '__main__':
    args = get_arguments()
    if args.data_dir:
        download_mets(args.data_dir)
