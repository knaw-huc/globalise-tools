#!/usr/bin/env python3
import glob
import json
import os
import re
from collections import defaultdict

import pagexml.helper.pagexml_helper as pxh
import pagexml.parser as px
import spacy
from icecream import ic
from intervaltree import IntervalTree
from loguru import logger
from pagexml.model.physical_document_model import PageXMLScan

from globalise_tools.model import LogicalAnchorRange

general_text_region_types = ['physical_structure_doc', 'pagexml_doc', 'text_region']
spacy_core = "nl_core_news_lg"
word_break_chars = '„'

logger.info(f"loading spacy core {spacy_core}")
nlp = spacy.load(spacy_core)


@logger.catch
def main(inv_nr: str) -> None:
    out_dir = f"out/{inv_nr}"
    os.makedirs(out_dir, exist_ok=True)

    line_ids_to_anchors = {}
    logical_anchor_range_for_line_anchor = defaultdict(lambda: LogicalAnchorRange(0, 0, 0, 0))
    lines = []
    paragraphs = []
    for path in pagexml_paths(inv_nr):
        untangle_file(path, line_ids_to_anchors, lines, logical_anchor_range_for_line_anchor, paragraphs)

    store_segmented_text(lines, f"{out_dir}/physical_text_store.json")
    store_segmented_text(paragraphs, f"{out_dir}/logical_text_store.json")

    # check_logical_to_physical(lines, paragraphs, logical_anchor_range_for_line_anchor)
    print_stats(lines, paragraphs)


def print_stats(lines, paragraphs):
    print("stats:")
    print(f"  {len(lines)} lines")
    print(f"  {len(paragraphs)} paragraphs")


def untangle_file(path, line_ids_to_anchors, lines, logical_anchor_range_for_line_anchor, paragraphs):
    logger.info(f"<= {path}")
    scan_doc: PageXMLScan = px.parse_pagexml_file(pagexml_file=path)
    for tr in scan_doc.get_text_regions_in_reading_order():
        if tr.lines:
            untangle_text_region(tr, line_ids_to_anchors, lines, logical_anchor_range_for_line_anchor, paragraphs)


def untangle_text_region(tr, line_ids_to_anchors, lines, logical_anchor_range_for_line_anchor, paragraphs):
    # print(defining_text_region_type(tr.types))
    lines_with_text = [l for l in tr.lines if l.text]
    if lines_with_text:
        lines_len = len(lines)
        tr_lines = []
        for l in lines_with_text:
            line_ids_to_anchors[l.id] = lines_len + len(tr_lines)
            line_text = re.sub(r' +', ' ', l.text)
            tr_lines.append(line_text)
            from_words = " ".join([w.text for w in l.words])
            if line_text != from_words:
                logger.error(f"line text '{line_text}' != joined words '{from_words}'")

        lines.extend(tr_lines)
        tr_text, line_ranges = pxh.make_text_region_text(lines_with_text, word_break_chars=word_break_chars)
        para_anchor = len(paragraphs)
        for line_range in line_ranges:
            line_anchor = line_ids_to_anchors[line_range['line_id']]
            start = line_range['start']
            end = line_range['end']
            logical_anchor_range_for_line_anchor[line_anchor] = LogicalAnchorRange(
                begin_logical_anchor=para_anchor,
                begin_char_offset=start,
                end_logical_anchor=para_anchor,
                end_char_offset_exclusive=end
            )
            if start > end:
                logger.error(f"start {start} > end {end}")
        paragraphs.append(tr_text)


def check_logical_to_physical(lines, paragraphs, logical_anchor_range_for_line_anchor):
    for k, v in logical_anchor_range_for_line_anchor.items():
        line_text = lines[k]
        para_substring = paragraphs[v.begin_logical_anchor][v.begin_char_offset:v.end_char_offset_exclusive]
        print(f"{k}: '{v}'")
        print(f"line {k:10}: '{line_text}'")
        prefix = f"para {v.begin_logical_anchor}[{v.begin_char_offset}:{v.end_char_offset_exclusive}]"
        print(
            f"{prefix:15}: '{para_substring}'")
        print()


def pagexml_paths(inv_nr: str) -> list[str]:
    return sorted(glob.glob(f"../pagexml/{inv_nr}/NL-HaNA_1.04.02_{inv_nr}_*.xml"))


def defining_text_region_type(types) -> str:
    return "/".join([t for t in types if t not in general_text_region_types])


def tokenize():
    text = "Rêrūm sit dignissimos quidem et sit dicta aperiam. Officiis autem dignissimos nihil. Illum ullam in cumque ex ducimus non. Fugit quam quis rem inventore nulla molestiae aut."
    itree = IntervalTree()

    doc = nlp(text)
    for token in doc:
        itree[token.idx:(token.idx + len(token))] = token.text
    print(text[0:10], sorted(itree[0:10]), sorted(itree.envelop(0, 10)))
    print(text[10:20], sorted(itree[10:20]), sorted(itree.envelop(10, 20)))
    print(text[20:30], sorted(itree[20:30]), sorted(itree.envelop(20, 30)))
    intervals = list(itree)
    as_json = json.dumps(intervals)
    print(as_json)
    t2 = IntervalTree(intervals)
    ic(t2[10:20])
    ic(json.dumps(t2))
    t2.merge_equals()


def store_segmented_text(segments: list[str], store_path: str):
    data = {"_ordered_segments": segments}
    store_json(data, store_path)


def store_json(data: any, store_path: str):
    logger.info(f"=> {store_path}")
    with open(store_path, 'w', encoding='UTF8') as filehandle:
        json.dump(data, filehandle, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    # tokenize()
    main("9999")
