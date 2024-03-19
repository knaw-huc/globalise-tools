#!/usr/bin/env python3
import argparse
from typing import List, Dict

import xmltodict
from loguru import logger


def get_paths(xml_dict: dict, prefix: str, elements_with_lists: List[str], element_attributes: dict) -> List[str]:
    paths = []
    attributes = [k[1:] for k in xml_dict.keys() if k.startswith('@')]
    root_element = prefix.split('.')[-1]

    if attributes:
        element_attributes.setdefault(root_element, set()).update(attributes)

    for key, value in xml_dict.items():
        if not key.startswith('@'):
            path = f"{prefix}.{key}"[1:]
            paths.append(path)

            if isinstance(value, dict):
                paths.extend(get_paths(value, f"{prefix}.{key}", elements_with_lists, element_attributes))
            elif isinstance(value, list):
                elements_with_lists.append(key)
                for item in value:
                    if isinstance(item, dict):
                        paths.extend(get_paths(item, f"{prefix}.{key}", elements_with_lists, element_attributes))

    return paths


def xml_fingerprint(xml_dicts: List[Dict[str, any]]) -> tuple:
    elements_with_lists = []
    element_attributes = {}
    unsorted_paths = []

    for xml in xml_dicts:
        unsorted_paths.extend(get_paths(xml, "", elements_with_lists, element_attributes))

    paths = sorted(set(unsorted_paths))
    elements_with_lists_set = sorted(set(elements_with_lists))

    new_paths = []
    for path in paths:
        for element in elements_with_lists_set:
            path = path.replace(f".{element}.", f".{element}[].")
            if path.endswith(f".{element}"):
                path += "[]"
        new_paths.append(path)

    return new_paths, element_attributes


@logger.catch
def get_arguments():
    parser = argparse.ArgumentParser(
        description="Show the (combined) unique element paths and element attributes of the provided xml files",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("xml_path",
                        nargs='+')
    return parser.parse_args()


@logger.catch
def show_xml_fingerprints(paths: List[str]):
    pages = []
    for path in paths:
        with open(path) as f:
            xml = f.read()
        page = xmltodict.parse(xml)
        pages.append(page)

    paths, attribute_dict = xml_fingerprint(pages)
    print("Paths:")
    for p in paths:
        print(f"  {p}")
    print()
    print("Attributes:")
    for e in sorted(attribute_dict.keys()):
        print(f"  {e}: {', '.join(attribute_dict[e])}")


if __name__ == '__main__':
    args = get_arguments()
    show_xml_fingerprints(args.xml_path)
