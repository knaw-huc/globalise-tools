#!/usr/bin/env python3
import csv
import glob
import json
import os
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

import pagexml.helper.pagexml_helper as pxh
import pagexml.parser as px
from loguru import logger
from tqdm import tqdm

import globalise_tools.tools as gt


class ParagraphTextExtractor:
    word_break_chars = '„'

    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.processed_file = f"{self.output_dir}/extract-paragraph-text-processed-inv-nrs.json"
        self.processed_inv_nrs = self.load_processed_files()

    def extract_paragraph_text(self):
        inv_nrs = sorted(
            [p.split("/")[-1] for p in glob.glob(f"{self.input_dir}/*") if os.path.isdir(p)])
        progress_bar = tqdm(inv_nrs)
        for inv_nr in progress_bar:
            if inv_nr in self.processed_inv_nrs:
                progress_bar.set_description(f"skipping {inv_nr}, already processed")
            else:
                self._process_inv(inv_nr, progress_bar)
                self.processed_inv_nrs.add(inv_nr)
                self.store_processed_files()

    def _pagexml_paths(self, inv_nr: str) -> list[str]:
        return sorted(glob.glob(f"{self.input_dir}/{inv_nr}/NL-HaNA_1.04.02_{inv_nr}_*.xml"))

    def _process_inv(self, inv_nr: str, bar):
        file_name = f"{self.output_dir}/{inv_nr}-paragraphs.tsv"
        bar.set_description(f"=> {file_name}")
        with open(file_name, mode='w', newline='') as file:
            writer = csv.writer(file, delimiter='\t')
            writer.writerow(["inv_nr", "page_no", "textarea_id", "paragraph_text"])
            for path in self._pagexml_paths(inv_nr):
                parts = path.split('/')
                page_no = parts[-1].split('_')[-1].replace('.xml', '')
                scan_doc = px.parse_pagexml_file(pagexml_file=path)
                for tr in [tr for tr in scan_doc.get_text_regions_in_reading_order() if gt.is_paragraph(tr)]:
                    lines_with_text = [l for l in tr.lines if l.text]
                    tr_text, line_ranges = pxh.make_text_region_text(lines_with_text,
                                                                     word_break_chars=self.word_break_chars)
                    if tr_text:
                        writer.writerow([inv_nr, page_no, tr.id, tr_text])

    def load_processed_files(self):
        if os.path.exists(self.processed_file):
            logger.info(f"<= {self.processed_file}")
            with open(self.processed_file) as f:
                processed = set(json.load(f))
        else:
            processed = set()
        return processed

    def store_processed_files(self):
        with open(self.processed_file, 'w') as f:
            json.dump(list(self.processed_inv_nrs), fp=f)


@logger.catch
def get_arguments():
    parser = ArgumentParser(
        description="Extract paragraph text from pagexml files",
        formatter_class=ArgumentDefaultsHelpFormatter)
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
