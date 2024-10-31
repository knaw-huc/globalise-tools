#!/usr/bin/env python3
import argparse
import csv
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from xml.etree.ElementTree import Element

from loguru import logger
from tqdm import tqdm


@dataclass
class Div:
    id: str
    order: int
    label: str


def to_div(element) -> Div:
    return Div(id=element.get("ID"), order=int(element.get("ORDER")), label=element.get("LABEL"))


def base_name(label: str) -> str:
    return label.replace('.tif', '').replace('.jpg', '').split('/')[-1]


def iiif_base_url(file_id: str, root) -> str:
    return root \
        .find(".//{http://www.loc.gov/METS/}file[@ID='" + file_id + "']") \
        .find(".//{http://www.loc.gov/METS/}FLocat") \
        .get('{http://www.w3.org/1999/xlink}href') \
        .replace('/info.json', '')


def na_url(file_path):
    file_name = file_path.split('/')[-1]
    file = file_name.replace('.xml', '')
    inv_nr = file_name.split('_')[2]
    return f"https://www.nationaalarchief.nl/onderzoeken/archief/1.04.02/invnr/{inv_nr}/file/{file}"


def base_prefix(record: dict) -> str:
    i = record['Instelling']
    t = record['Toegangsnummer']
    inr = record['Inventarisnummer']
    return f"{i}_{t}_{inr}"


def to_mets_id(url: str) -> str:
    return url.split('/')[-1]


def to_mapping_pair(div: Div, root: Element) -> (str, str):
    b = base_name(div.label)
    u = iiif_base_url(div.id + "IIP", root)
    return b, u


def get_mappings(file_path: str) -> list:
    with open(file_path) as f:
        xml = f.read()
    root = ET.fromstring(xml)
    divs = [to_div(e) for e in root.findall(".//{http://www.loc.gov/METS/}div[@ORDERLABEL='record (item)']")]
    mappings = []
    for d in divs:
        mappings.append(to_mapping_pair(d, root))
    return mappings


def print_missing_files(missing_files):
    if len(missing_files) > 0:
        print("missing mets files:")
        for f in missing_files:
            print(f)


@logger.catch
def map_pagexml_to_iiif_url(data_dir: str):
    mets_csv = f"{data_dir}/NL-HaNA_1.04.02_mets.csv"
    mapping_csv = f"{data_dir}/iiif-url-mapping.csv"
    print(f"reading {mets_csv}...")
    with open(mets_csv) as f:
        records = [r for r in csv.DictReader(f) if r['METS link'] != '']

    missing_files = []
    print(f"writing {mapping_csv}...")
    with open(mapping_csv, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["pagexml_id", "iiif_base_url"])
        bar = tqdm(range(len(records)))
        for i in bar:
            r = records[i]
            url = r['METS link']
            mets_id = to_mets_id(url)
            bar.set_description(f"processing {mets_id}...")
            file_path = f'{data_dir}/mets/{mets_id}.xml'
            if Path(file_path).is_file():
                for m in get_mappings(file_path):
                    writer.writerow(m)
            else:
                missing_files.append(file_path)
    print_missing_files(missing_files)


@logger.catch
def get_arguments():
    parser = argparse.ArgumentParser(
        description="Create a csv file mapping a pagexml base name to a IIIF base url",
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
        map_pagexml_to_iiif_url(args.data_dir)
