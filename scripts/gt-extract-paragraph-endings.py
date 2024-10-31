#!/usr/bin/env python3
import csv
import json
from collections import defaultdict

import spacy
from loguru import logger

file = "/Users/bram/workspaces/globalise/globalise-tools/data/globalise-word-joins-MH.csv"


@logger.catch
def main():
    with open(file) as f:
        reader = csv.DictReader(f)
        records = [r for r in reader]
    np_records = [r for r in records if r['new paragraph?']]

    # extract_tokenized_paragraph_markers(np_records)
    paragraph_line_markers_per_pagexml = defaultdict(list)
    for np in np_records:
        name = np['scan']
        line_0 = np['line n']
        line_1 = np['line n+1']
        paragraph_line_markers_per_pagexml[name].append((line_0, line_1))
    print(json.dumps(paragraph_line_markers_per_pagexml, indent=2))


def tokenize(nlp, text: str) -> list[str]:
    tokens = []
    doc = nlp(text)
    for sentence in doc.sents:
        for token in [t for t in sentence if t.text != "\n"]:
            tokens.append(token.text)
    return tokens


def extract_tokenized_paragraph_markers(np_records):
    spacy_core = "nl_core_news_lg"
    nlp = spacy.load(spacy_core)
    paragraph_markers = []
    for np in np_records:
        line_0 = np['line n']
        line_1 = np['line n+1']
        line_0_tokens = tokenize(nlp, line_0)
        line_1_tokens = tokenize(nlp, line_1)
        paragraph_markers.append((line_0_tokens, line_1_tokens))
    print(json.dumps(paragraph_markers, indent=2))


if __name__ == '__main__':
    main()
