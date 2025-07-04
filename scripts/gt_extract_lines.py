#!/usr/bin/env python3
import csv
import glob
import os
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

import pagexml.parser as px
from loguru import logger


def main():
    args = get_arguments()
    run(args.input_directory, args.output_directory, args.force)


@logger.catch
def run(base_pagexml_path: str, output_directory: str, force: bool):
    inv_nrs = sorted(
        [p.split("/")[-1] for p in glob.glob(f"{base_pagexml_path}/*") if os.path.isdir(p)])
    for i in inv_nrs:
        process_inv(i, base_pagexml_path, output_directory, force)


def pagexml_paths(inv_nr: str, base_pagexml_path: str) -> list[str]:
    return sorted(glob.glob(f"{base_pagexml_path}/{inv_nr}/NL-HaNA_1.04.02_{inv_nr}_*.xml"))


def process_inv(inv_nr: str, base_pagexml_path: str, output_directory: str, force: bool):
    file_name = f"{output_directory}/{inv_nr}-lines.tsv"
    if not os.path.exists(file_name) or force:
        print(f"=> {file_name}")
        with open(file_name, mode='w', newline='') as file:
            writer = csv.writer(file, delimiter='\t')
            writer.writerow(["inv_nr", "page_no", "textregion_id", "textregion_type", "line_id", "line_text"])
            for path in pagexml_paths(inv_nr, base_pagexml_path):
                parts = path.split('/')
                page_no = parts[-1].split('_')[-1].replace('.xml', '')
                scan_doc = px.parse_pagexml_file(pagexml_file=path)
                for tr in scan_doc.get_text_regions_in_reading_order():
                    if tr.lines:
                        for l in tr.lines:
                            if l.text:
                                writer.writerow([inv_nr, page_no, tr.id, tr.type[-1], l.id, l.text])
    else:
        print(f"=> skipping existing file {file_name}")


@logger.catch
def get_arguments():
    parser = ArgumentParser(
        description="Extract line text from pagexml files",
        formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i",
                        "--input-directory",
                        required=True,
                        help="The directory where the original PageXML files are stored, grouped by inventory number.",
                        type=str)
    parser.add_argument("-o",
                        "--output-directory",
                        help="The directory to write the output files in",
                        default=".",
                        type=str
                        )
    parser.add_argument("-f",
                        "--force",
                        help="Overwrite existing files",
                        )
    return parser.parse_args()


if __name__ == '__main__':
    main()
