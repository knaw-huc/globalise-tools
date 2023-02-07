#!/usr/bin/env python3
import glob
import json
from typing import List

from icecream import ic

from globalise_tools.webanno_tsv_reader import read_webanno_tsv, Token

data_dir = "data/inception_output"


def main():
    for path in web_anno_file_paths(data_dir):
        doc_id = make_doc_id(path)
        word_annotations, token_annotations = load_word_and_token_annotations(doc_id)

        doc = read_webanno_tsv(path)
        tokens = doc.tokens
        annotations = doc.annotations

        selection = annotations
        ic(selection)

        whole_tokens = [t for t in tokens if "." not in t.token_num]
        token_idx = {token_id(t): i for i, t in enumerate(whole_tokens)}

        for annotation in selection:
            print(annotation)
            text1 = annotation.text
            print(text1)
            print([f"{t.sentence_num}-{t.token_num} {t.text}" for t in annotation.tokens])
            ta = [token_annotations[token_idx[token_id(t).split('.')[0]]] for t in annotation.tokens]
            ta_text_list = [a["metadata"]["text"] for a in ta]
            text2 = " ".join(ta_text_list)
            print(text2)
            print()
            if text1 != text2:
                ic(text1, text2)


def token_id(token: Token) -> str:
    return f"{token.sentence_num}-{token.token_num}"


def web_anno_file_paths(folder: str) -> List[str]:
    return glob.glob(f"{folder}/*.tsv")


def load_word_and_token_annotations(doc_id):
    with open(f"out/{doc_id}-metadata.json") as jf:
        metadata = json.load(jf)
    # ic(metadata)
    word_annotations = [a for a in metadata["annotations"] if a["type"] == "tt:Word"]
    token_annotations = [a for a in metadata["annotations"] if a["type"] == "tt:Token"]
    # ic(word_annotations)
    return word_annotations, token_annotations


def make_doc_id(p):
    return p.split('/')[-1].replace('.tsv', '')


if __name__ == '__main__':
    main()
