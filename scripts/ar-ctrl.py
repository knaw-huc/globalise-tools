#!/usr/bin/env python3
import argparse
import json
from itertools import zip_longest

from annorepo.client import AnnoRepoClient
from icecream import ic

ids = ["NL-HaNA_1.04.02_1092_0017",
       "NL-HaNA_1.04.02_1092_0018",
       "NL-HaNA_1.04.02_1092_0019",
       "NL-HaNA_1.04.02_1092_0020",
       "NL-HaNA_1.04.02_1092_0021",
       "NL-HaNA_1.04.02_1297_0019",
       "NL-HaNA_1.04.02_1297_0020",
       "NL-HaNA_1.04.02_1297_0021",
       "NL-HaNA_1.04.02_1297_0022",
       "NL-HaNA_1.04.02_1297_0023",
       "NL-HaNA_1.04.02_1297_0024",
       "NL-HaNA_1.04.02_1297_0025",
       "NL-HaNA_1.04.02_1297_0026",
       "NL-HaNA_1.04.02_1297_0027",
       "NL-HaNA_1.04.02_1297_0028",
       "NL-HaNA_1.04.02_1297_0029",
       "NL-HaNA_1.04.02_1297_0030",
       "NL-HaNA_1.04.02_1297_0031",
       "NL-HaNA_1.04.02_1297_0032",
       "NL-HaNA_1.04.02_1297_0033",
       "NL-HaNA_1.04.02_1297_0034",
       "NL-HaNA_1.04.02_1297_0035",
       "NL-HaNA_1.04.02_1297_0036",
       "NL-HaNA_1.04.02_1297_0037",
       "NL-HaNA_1.04.02_1297_0038",
       "NL-HaNA_1.04.02_1297_0039",
       "NL-HaNA_1.04.02_1297_0040",
       "NL-HaNA_1.04.02_1297_0041",
       "NL-HaNA_1.04.02_1297_0042",
       "NL-HaNA_1.04.02_1297_0043",
       "NL-HaNA_1.04.02_1297_0044",
       "NL-HaNA_1.04.02_1297_0045",
       "NL-HaNA_1.04.02_1297_0046",
       "NL-HaNA_1.04.02_1297_0047",
       "NL-HaNA_1.04.02_1297_0048",
       "NL-HaNA_1.04.02_1297_0049",
       "NL-HaNA_1.04.02_1297_0050",
       "NL-HaNA_1.04.02_1297_0051",
       "NL-HaNA_1.04.02_1297_0052",
       "NL-HaNA_1.04.02_1297_0053",
       "NL-HaNA_1.04.02_1297_0054",
       "NL-HaNA_1.04.02_1297_0055",
       "NL-HaNA_1.04.02_1297_0056",
       "NL-HaNA_1.04.02_1297_0057",
       "NL-HaNA_1.04.02_1589_0019",
       "NL-HaNA_1.04.02_1589_0020",
       "NL-HaNA_1.04.02_1589_0021",
       "NL-HaNA_1.04.02_1589_0048",
       "NL-HaNA_1.04.02_1589_0049",
       "NL-HaNA_1.04.02_1589_0052",
       "NL-HaNA_1.04.02_1589_0053",
       "NL-HaNA_1.04.02_1589_0054",
       "NL-HaNA_1.04.02_1589_0055",
       "NL-HaNA_1.04.02_1589_0056",
       "NL-HaNA_1.04.02_1859_0115",
       "NL-HaNA_1.04.02_1859_0116",
       "NL-HaNA_1.04.02_1859_0117",
       "NL-HaNA_1.04.02_1859_0118",
       "NL-HaNA_1.04.02_1859_0119",
       "NL-HaNA_1.04.02_1859_0120",
       "NL-HaNA_1.04.02_1859_0121",
       "NL-HaNA_1.04.02_1859_0122",
       "NL-HaNA_1.04.02_1859_0123",
       "NL-HaNA_1.04.02_1859_0124",
       "NL-HaNA_1.04.02_1859_0125",
       "NL-HaNA_1.04.02_1859_0126",
       "NL-HaNA_1.04.02_1859_0127",
       "NL-HaNA_1.04.02_1859_0128",
       "NL-HaNA_1.04.02_1859_0129",
       "NL-HaNA_1.04.02_1859_0130",
       "NL-HaNA_1.04.02_1859_0131",
       "NL-HaNA_1.04.02_1859_0132",
       "NL-HaNA_1.04.02_1859_0133",
       "NL-HaNA_1.04.02_1859_0134",
       "NL-HaNA_1.04.02_1859_0135",
       "NL-HaNA_1.04.02_7573_0077",
       "NL-HaNA_1.04.02_7573_0078",
       "NL-HaNA_1.04.02_7573_0183",
       "NL-HaNA_1.04.02_7573_0184",
       "NL-HaNA_1.04.02_7573_0185",
       "NL-HaNA_1.04.02_7573_0186",
       "NL-HaNA_1.04.02_7573_0187",
       "NL-HaNA_1.04.02_7573_0188",
       "NL-HaNA_1.04.02_7573_0189",
       "NL-HaNA_1.04.02_7573_0190"]

wa = ["out/NL-HaNA_1.04.02_1092_0017_0021-web-annotations.json",
      "out/NL-HaNA_1.04.02_1297_0019_0057-web-annotations.json",
      "out/NL-HaNA_1.04.02_1589_0019_0021-web-annotations.json",
      "out/NL-HaNA_1.04.02_1589_0048_0049-web-annotations.json",
      "out/NL-HaNA_1.04.02_1589_0052_0056-web-annotations.json",
      "out/NL-HaNA_1.04.02_1859_0115_0135-web-annotations.json",
      "out/NL-HaNA_1.04.02_7573_0077_0078-web-annotations.json",
      "out/NL-HaNA_1.04.02_7573_0183_0190-web-annotations.json"]


def access_annorepo(base_uri: str, api_key: str):
    arc = AnnoRepoClient(base_uri, api_key=api_key)
    ic(arc.get_about())

    # container_name = "tmp"
    container_name = "globalise-demo-1"
    make_container(arc, container_name)
    upload_annotations(arc, container_name)
    # r = arc.delete_container(container_name, eTag)
    # ic(r)


def make_chunks_of_size(chunk_size, big_list):
    chunked_list = [big_list(item) for item in big_list(zip_longest(*[iter(big_list)] * chunk_size, fillvalue=''))]
    chunked_list[-1] = [x for x in chunked_list[-1] if x]
    return chunked_list


def upload_annotations(arc, container_name):
    for a in wa:
        with open(a) as f:
            annotations = json.load(f)

        chunks = make_chunks_of_size(500, annotations)
        for annos in chunks:
            r = arc.add_annotations(container_name, annotation_list=annos)
            # ic(r)


def make_container(arc, container_name):
    (eTag, location, json_content) = arc.create_container(container_name, "Container for globalise annotations")
    ic(eTag, location, json_content)


def get_arguments():
    parser = argparse.ArgumentParser(
        description="Access an annorepo instance",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-a",
                        "--annorepo-url",
                        required=True,
                        help="The url to the annorepo instance",
                        type=str)
    parser.add_argument("-k",
                        "--api-key",
                        required=False,
                        help="The API key for authorization",
                        type=str)
    return parser.parse_args()


if __name__ == '__main__':
    args = get_arguments()
    access_annorepo(args.annorepo_url, args.api_key)
