#!/usr/bin/env python3

import csv
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List
from xml.etree.ElementTree import Element

data_dir = '/Users/bram/workspaces/globalise/globalise-tools/data'


@dataclass
class Div:
    id: str
    order: int
    label: str


def to_div(element) -> Div:
    return Div(id=element.get("ID"), order=int(element.get("ORDER")), label=element.get("LABEL"))


def base_name(label: str) -> str:
    return label.replace('.tif', '').split('/')[-1]


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


def get_mappings(record) -> List:
    url = record['METS link']
    mets_id = to_mets_id(url)
    with open(f'{data_dir}/mets/{mets_id}.xml') as f:
        xml = f.read()
    root = ET.fromstring(xml)
    divs = [to_div(e) for e in root.findall(".//{http://www.loc.gov/METS/}div[@ORDERLABEL='record (item)']")]
    mappings = []
    for d in divs:
        mappings.append(to_mapping_pair(d, root))
    return mappings


def main():
    with open(f'{data_dir}/NL-HaNA_1.04.02_mets.csv') as f:
        records = [r for r in csv.DictReader(f) if r['METS link'] != '']

    mappings = []
    for r in records:
        m = get_mappings(r)
        mappings.extend(m)

    with open(f"{data_dir}/iiif-url-mapping.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(["pagexml_id", "iiif_base_url"])
        for m in mappings:
            writer.writerow(m)


if __name__ == '__main__':
    main()
