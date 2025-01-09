#!/usr/bin/env python3
import argparse

import spacy
from cassis import *
from loguru import logger
from pagexml.parser import parse_pagexml_file

import globalise_tools.tools as gt
from globalise_tools.model import CAS_SENTENCE, CAS_TOKEN, CAS_PARAGRAPH, CAS_MARGINALIUM, CAS_HEADER

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

    text, marginalia_ranges, header_range, paragraph_ranges, word_interval_tree = gt.extract_paragraph_text(scan_doc)

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
        MarginaliumAnnotation = cas.typesystem.get_type(CAS_MARGINALIUM)
        HeaderAnnotation = cas.typesystem.get_type(CAS_HEADER)
        doc = nlp(text)
        for sentence in doc.sents:
            cas.add(SentenceAnnotation(begin=sentence.start_char, end=sentence.end_char))
            for token in [t for t in sentence if t.text != "\n"]:
                begin = token.idx
                end = token.idx + len(token.text)
                cas.add(TokenAnnotation(begin=begin, end=end))

        for pr in marginalia_ranges:
            cas.add(MarginaliumAnnotation(begin=pr[0], end=pr[1]))
        if header_range:
            cas.add(HeaderAnnotation(begin=header_range[0], end=header_range[1]))
        for pr in paragraph_ranges:
            cas.add(ParagraphAnnotation(begin=pr[0], end=pr[1]))

        # print_annotations(cas)

        cas_xmi = output_path(page_xml_path)
        logger.info(f"=> {cas_xmi}")
        cas.to_xmi(cas_xmi, pretty_print=True)


if __name__ == '__main__':
    args = get_arguments()
    if args.page_xml_path:
        convert(args.page_xml_path)
