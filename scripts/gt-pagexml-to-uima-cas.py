#!/usr/bin/env python3
import argparse
from typing import Tuple, List

import spacy
from cassis import *
from icecream import ic
from loguru import logger
from pagexml.model.physical_document_model import PageXMLTextRegion
from pagexml.parser import parse_pagexml_file

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


def is_paragraph(text_region: PageXMLTextRegion) -> bool:
    return text_region.type[-1] == "paragraph"


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

        SentenceAnnotation = cas.typesystem.get_type("de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence")
        TokenAnnotation = cas.typesystem.get_type("de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token")
        ParagraphAnnotation = cas.typesystem.get_type("de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Paragraph")
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


def paragraph_text(lines: List[str]) -> str:
    break_char = "„"
    # ic(lines)
    for i in range(0, len(lines) - 1):
        line0 = lines[i]
        line1 = lines[i + 1]
        if line0.endswith(break_char):
            lines[i] = line0.rstrip(break_char)
            lines[i + 1] = line1.lstrip(break_char)
        else:
            lines[i] = f"{line0} "
    # ic(lines)
    return "".join(lines) + "\n"


def extract_paragraph_text(scan_doc) -> Tuple[str, List[Tuple[int, int]]]:
    paragraph_ranges = []
    offset = 0
    text = ""
    for tr in scan_doc.get_text_regions_in_reading_order():
        if is_paragraph(tr):
            lines = []
            for line in tr.lines:
                if line.text:
                    lines.append(line.text)
            text += paragraph_text(lines)
            text_len = len(text)
            paragraph_ranges.append((offset, text_len))
            offset = text_len
    return text, paragraph_ranges


def print_annotations(cas):
    for a in cas.views[0].get_all_annotations():
        print(a)
        print(f"'{a.get_covered_text()}'")
        print()


def join_words(px_words):
    text = ""
    last_text_region = None
    last_line = None
    for w in px_words:
        if w.text_region_id == last_text_region:
            if w.line_id != last_line:
                text += "|\n"
            text += " "
        else:
            text += "\n\n"
        text += w.text
        last_text_region = w.text_region_id
        last_line = w.line_id
    return text.strip()


if __name__ == '__main__':
    args = get_arguments()
    if args.page_xml_path:
        convert(args.page_xml_path)
