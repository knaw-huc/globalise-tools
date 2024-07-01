#!/usr/bin/env python3
import argparse
import csv
import glob
import os

import pagexml.helper.pagexml_helper as pxh
import pagexml.parser as px
from loguru import logger

import globalise_tools.tools as gt


class ParagraphTextExtractor:
    word_break_chars = '„'

    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = input_dir
        self.output_dir = output_dir

    def extract_paragraph_text(self):
        inv_nrs = sorted(
            [p.split("/")[-1] for p in glob.glob(f"{self.input_dir}/*") if os.path.isdir(p)])
        for i in inv_nrs:
            self._process_inv(i)

    def _pagexml_paths(self, inv_nr: str) -> list[str]:
        return sorted(glob.glob(f"{self.input_dir}/{inv_nr}/NL-HaNA_1.04.02_{inv_nr}_*.xml"))

    def _process_inv(self, inv_nr: str):
        file_name = f"{self.output_dir}/{inv_nr}-paragraphs.tsv"
        logger.info(f"=> {file_name}")
        with open(file_name, mode='w', newline='') as file:
            writer = csv.writer(file, delimiter='\t')
            writer.writerow(["inv_nr", "page_no", "textarea_id", "paragraph_text"])
            for path in self._pagexml_paths(inv_nr):
                parts = path.split('/')
                page_no = parts[-1].split('_')[-1].replace('.xml', '')
                # logger.info(f"<= {path}")
                scan_doc = px.parse_pagexml_file(pagexml_file=path)
                for tr in [tr for tr in scan_doc.get_text_regions_in_reading_order() if gt.is_paragraph(tr)]:
                    lines_with_text = [l for l in tr.lines if l.text]
                    tr_text, line_ranges = pxh.make_text_region_text(lines_with_text,
                                                                     word_break_chars=self.word_break_chars)
                    if tr_text:
                        writer.writerow([inv_nr, page_no, tr.id, tr_text])


@logger.catch
def get_arguments():
    parser = argparse.ArgumentParser(
        description="Extract paragraph text from pagexml files",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i",
                        "--input-directory",
                        required=True,
                        help="The directory where the original PageXML files are stored, grouped by inventory number.",
                        type=str)
    parser.add_argument("-o",
                        "--output-directory",
                        help="The directory to write the output files in",
                        type=str
                        )
    return parser.parse_args()


if __name__ == '__main__':
    args = get_arguments()
    if args.input_directory:
        ParagraphTextExtractor(args.input_directory, args.output_directory).extract_paragraph_text()
