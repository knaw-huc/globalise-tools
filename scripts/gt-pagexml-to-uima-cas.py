#!/usr/bin/env python3
import argparse
from typing import Tuple, List

import spacy
from cassis import *
from loguru import logger
from pagexml.parser import parse_pagexml_file

from globalise_tools.model import CAS_SENTENCE, CAS_TOKEN, CAS_PARAGRAPH
from globalise_tools.tools import is_paragraph, paragraph_text

typesystem_xml = 'data/typesystem.xml'
spacy_core = "nl_core_news_lg"

logger.info(f"loading {spacy_core}")
nlp = spacy.load(spacy_core)


@logger.catch
def get_arguments():
    parser = argparse.ArgumentParser(
        description="Convert a PageXML file to UAMI CAS XMI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("page_xml_path",
                        help="The path to the pagexml file.",
                        type=str)
    return parser.parse_args()


def output_path(page_xml_path: str) -> str:
    base = page_xml_path.split("/")[-1].replace(".xml", "")
    return f"out/{base}.xmi"


@logger.catch
def convert(page_xml_path: str):
    logger.info(f"<= {page_xml_path}")
    scan_doc = parse_pagexml_file(page_xml_path)

    text, paragraph_ranges = extract_paragraph_text(scan_doc)

    if not text:
        logger.warning(f"no paragraph text found in {page_xml_path}")
    else:
        logger.info(f"<= {typesystem_xml}")
        with open(typesystem_xml, 'rb') as f:
            typesystem = load_typesystem(f)

        cas = Cas(typesystem=typesystem)
        cas.sofa_string = text
        cas.sofa_mime = "text/plain"

        SentenceAnnotation = cas.typesystem.get_type(CAS_SENTENCE)
        TokenAnnotation = cas.typesystem.get_type(CAS_TOKEN)
        ParagraphAnnotation = cas.typesystem.get_type(CAS_PARAGRAPH)
        doc = nlp(text)
        for sentence in doc.sents:
            cas.add(SentenceAnnotation(begin=sentence.start_char, end=sentence.end_char))
            for token in [t for t in sentence if t.text != "\n"]:
                begin = token.idx
                end = token.idx + len(token.text)
                cas.add(TokenAnnotation(begin=begin, end=end))

        for pr in paragraph_ranges:
            cas.add(ParagraphAnnotation(begin=pr[0], end=pr[1]))

        # print_annotations(cas)

        cas_xmi = output_path(page_xml_path)
        logger.info(f"=> {cas_xmi}")
        cas.to_xmi(cas_xmi, pretty_print=True)


def extract_paragraph_text(scan_doc) -> Tuple[str, List[Tuple[int, int]]]:
    paragraph_ranges = []
    offset = 0
    text = ""
    for tr in scan_doc.get_text_regions_in_reading_order():
        logger.info(f"text_region: {tr.id}")
        logger.info(f"type: {tr.type[-1]}")
        line_text = [l.text for l in tr.lines]
        for t in line_text:
            logger.info(f"line: {t}")
        if is_paragraph(tr):
            lines = []
            for line in tr.lines:
                if line.text:
                    lines.append(line.text)
            ptext = paragraph_text(lines)
            text += ptext
            text_len = len(text)
            paragraph_ranges.append((offset, text_len))
            offset = text_len
            logger.info(f"para: {ptext}")
        logger.info("")
    return text, paragraph_ranges


if __name__ == '__main__':
    args = get_arguments()
    if args.page_xml_path:
        convert(args.page_xml_path)
