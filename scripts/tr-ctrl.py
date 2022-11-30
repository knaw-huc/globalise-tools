#!/usr/bin/env python3
import argparse

from icecream import ic
from textrepo.client import TextRepoClient

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


def access_textrepo(base_uri: str, api_key: str):
    trc = TextRepoClient(base_uri, api_key=api_key)
    set_file_types(trc)
    for external_id in ids:
        try:
            m = trc.find_file_metadata(external_id=external_id, type_name="pagexml")
            ic(external_id, m)
        except:
            print(f"external id {external_id} not found")


def set_file_types(trc):
    type_name = "conll"
    if not has_file_type(trc, type_name):
        trc.create_file_type(name=type_name, mimetype="application/conll2002+txt")
    type_name = "segmented_text"
    if not has_file_type(trc, type_name):
        trc.create_file_type(name=type_name, mimetype="application/json")


def has_file_type(trc, type_name):
    file_types = trc.read_file_types()
    return type_name in {ft.name for ft in file_types}


def get_arguments():
    parser = argparse.ArgumentParser(
        description="Access a textrepo instance",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-t",
                        "--textrepo-url",
                        required=True,
                        help="The url to the textrepo instance",
                        type=str)
    parser.add_argument("-a",
                        "--api-key",
                        required=False,
                        help="The API key for authorization",
                        type=str)
    return parser.parse_args()


if __name__ == '__main__':
    args = get_arguments()
    access_textrepo(args.textrepo_url, args.api_key)
