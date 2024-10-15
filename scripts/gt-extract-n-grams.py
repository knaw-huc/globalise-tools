#!/usr/bin/env python3
import argparse
from collections import Counter

import pagexml.helper.pagexml_helper as pxh
import pagexml.parser as pxp
from loguru import logger


@logger.catch
def get_arguments():
    parser = argparse.ArgumentParser(
        description="Extract paragraph text from a PageXML file, and export the n-grams",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("page_xml_path",
                        help="The path to the pagexml file.",
                        nargs='+',
                        type=str)
    return parser.parse_args()


word_break_chars = '„¬'


def extract_ngrams(page_xml_paths: list[str]):
    word_counter = Counter()
    for page_xml_path in page_xml_paths:
        logger.info(f"<= {page_xml_path}")
        scan_doc = pxp.parse_pagexml_file(page_xml_path)
        for tr in scan_doc.get_text_regions_in_reading_order():
            tr_text, _ = pxh.make_text_region_text(tr.lines,
                                                   word_break_chars=word_break_chars)
            if tr_text:
                tr_words = [w.lstrip("(").rstrip(".,):") for w in tr_text.split()]
                word_counter.update([w for w in tr_words if w])
    sorted_words = sorted(word_counter.keys(), key=lambda w: w.lower())
    for w in sorted_words:
        print(f"{w} | {word_counter[w]}")
    print("most common words:")
    for c in word_counter.most_common(100):
        print(c)


if __name__ == '__main__':
    args = get_arguments()
    if args.page_xml_path:
        extract_ngrams(args.page_xml_path)
