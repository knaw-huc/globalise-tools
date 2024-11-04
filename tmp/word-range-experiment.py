#!/usr/bin/env python3
import re

import cassis
import pagexml.parser as px
import spacy
from icecream import ic
from intervaltree import IntervalTree
from loguru import logger

import globalise_tools.tools as gt

inv_nr = "10009"
page_nr = "0407"
page_xml_path = f"/Users/bram/c/data/globalise/pagexml/{inv_nr}/NL-HaNA_1.04.02_{inv_nr}_{page_nr}.xml"
xmi_path = f"/Users/bram/c/data/globalise/ner/xmicas/{inv_nr}/NL-HaNA_1.04.02_{inv_nr}_{page_nr}.xmi"
typesystem_path = "data/typesystem.xml"
word_break_chars = '„¬'

spacy_core = "nl_core_news_lg"


def main():
    logger.info(f"loading {spacy_core}")
    nlp = spacy.load(spacy_core)

    logger.info(f"<= {page_xml_path}")
    scan_doc = px.parse_pagexml_file(pagexml_file=page_xml_path)
    itree = IntervalTree()
    paragraphs = []
    paragraph_words = []
    headers = []
    header_words = []
    marginalia = []
    marginalia_words = []
    for tr in scan_doc.get_text_regions_in_reading_order():
        # lines_with_text = [l for l in tr.lines if l.text]
        # tr_text, line_ranges = pxh.make_text_region_text(lines_with_text, word_break_chars=word_break_chars)
        if gt.is_marginalia(tr):
            ptext = gt.joined_lines(tr)
            if ptext:
                marginalia.append(ptext)
                marginalia_words.extend(tr.get_words())
        if gt.is_header(tr):
            ptext = gt.joined_lines(tr)
            if ptext:
                headers.append(ptext)
                header_words.extend(tr.get_words())
        if gt.is_paragraph(tr) or gt.is_signature(tr):
            ptext = gt.joined_lines(tr)
            if ptext:
                paragraphs.append(ptext)
                paragraph_words.extend(tr.get_words())

    marginalia_ranges = []
    header_range = None
    paragraph_ranges = []
    offset = 0
    text = ""
    for m in marginalia:
        text += m
        text_len = len(text)
        marginalia_ranges.append((offset, text_len))
        offset = text_len
    if headers:
        h = headers[0]
        text += f"\n{h}\n"
        text_len = len(text)
        header_range = (offset + 1, text_len - 1)
        offset = text_len
    for m in paragraphs:
        text += m
        text_len = len(text)
        paragraph_ranges.append((offset, text_len))
        offset = text_len

    start = 0
    all_words = marginalia_words + header_words + paragraph_words
    for word in all_words:
        word_text = word.text
        word_len = len(word_text)
        offset = text.find(word_text, start)
        if offset == -1:
            logger.info("offset==-1")
            cleaned_text = re.sub(f'[{word_break_chars}]', '', word_text)
            offset = text.find(cleaned_text, start)
            word_len = len(cleaned_text)
        begin = offset
        end = offset + word_len
        sub = text[begin:end]
        ic(offset, word_text, sub)
        itree[begin:end] = word

        start = offset + word_len - 1
    print()

    doc = nlp(text)
    for sentence in doc.sents:
        for token in [t for t in sentence if t.text != "\n"]:
            begin = token.idx
            end = token.idx + len(token.text)
            overlapping_intervals = sorted(list(itree[begin:end]))
            token_text = f"({begin}:{end}) {token.text}"
            overlapping_words = [f"({i[0]}:{i[1]}) {i[2].text}" for i in overlapping_intervals]
            if len(overlapping_words) != 1 or (len(overlapping_words) == 1 and overlapping_words[0] != token_text):
                ic(token_text, overlapping_words)

    entity_annotations = load_entity_annotations()
    for entity in entity_annotations:
        ic(entity)
        begin = entity['begin']
        end = entity['end']
        overlapping_intervals = sorted(list(itree[begin:end]))
        entity_text = f"({begin}:{end}) {entity.get_covered_text()}"
        overlapping_words = [f"({i[0]}:{i[1]}) {i[2].text}" for i in overlapping_intervals]
        ic(entity_text, overlapping_words)

    # if tr_text:
    #     ic(tr_text)
    #     ic(line_ranges)
    #     start = 0
    #     calc_start = 0
    #     for word in tr.get_words():
    #         ic(word)
    #         wt = word.text
    #         offset = tr_text.find(wt, start)
    #         if offset == -1:
    #             logger.info("offset==-1")
    #             offset = calc_start
    #         else:
    #             calc_start = offset
    #         sub = tr_text[offset:offset + len(wt)]
    #         ic(offset, wt, sub)
    #         start = offset
    #         calc_start += len(wt) + 1
    #     print()


def load_entity_annotations():
    logger.info(f"<= {typesystem_path}")
    with open(typesystem_path, 'rb') as f:
        typesystem = cassis.load_typesystem(f)
    logger.info(f"<= {xmi_path}")
    with open(xmi_path, 'rb') as f:
        cas = cassis.load_cas_from_xmi(f, typesystem=typesystem)
    entity_annotations = [a for a in cas.views[0].get_all_annotations() if
                          a.type.name == "de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity" and a.value]
    return entity_annotations


if __name__ == '__main__':
    main()
