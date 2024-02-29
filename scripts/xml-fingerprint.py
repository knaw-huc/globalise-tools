#!/usr/bin/env python3
import argparse
from typing import List, Dict

import xmltodict
from loguru import logger


def as_paths(d, prefix, elements_with_lists, element_attributes: dict):
    paths = []
    elements = [k for k in d.keys() if not k.startswith('@')]
    attributes = [k[1:] for k in d.keys() if k.startswith('@')]
    root_element = prefix.split('.')[-1]
    if attributes:
        if root_element not in element_attributes:
            element_attributes[root_element] = set()
        element_attributes[root_element].update(attributes)

    if elements:
        for e in elements:
            paths.append(f"{prefix}.{e}"[1:])
            if isinstance(d[e], dict):
                paths.extend(as_paths(d[e], f"{prefix}.{e}", elements_with_lists, element_attributes))
            elif isinstance(d[e], list):
                elements_with_lists.append(e)
                for i in d[e]:
                    if isinstance(i, dict):
                        paths.extend(as_paths(i, f"{prefix}.{e}", elements_with_lists, element_attributes))
            elif isinstance(d[e], str):
                pass
            else:
                print(type(d[e]))
    return paths


def xml_fingerprint(xml_dicts: List[Dict[str, any]]):
    elements_with_lists = []
    element_attributes = {}
    unsorted_paths = []
    for xml in xml_dicts:
        unsorted_paths.extend(as_paths(xml, "", elements_with_lists, element_attributes))
    paths = set(sorted(unsorted_paths))
    elements_with_lists_set = set(sorted(elements_with_lists))
    new_paths = []
    for path in sorted(paths):
        for e in elements_with_lists_set:
            path = path.replace(f".{e}.", f".{e}[].")
            if path.endswith(f".{e}"):
                path = path + "[]"
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
