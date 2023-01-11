#!/usr/bin/env python3
import glob
import json
from typing import List

from icecream import ic

from globalise_tools.webanno_tsv_tools import process_webanno_tsv_file2

data_dir = "data/inception_output"


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


def main():
    for p in web_anno_file_paths(data_dir):
        # ic(p)
        doc_id = make_doc_id(p)
        word_annotations, token_annotations = load_word_and_token_annotations(doc_id)
        tokens, annotations = process_webanno_tsv_file2(p)

        selection = [a for a in annotations if len(a.layers) > 1]
        ic(selection)

        for a in [a for a in annotations]:
            print(a)
            print(a.text)
            print(json.dumps(a.layers[0].elements[0].fields, indent=2))
            anno_tokens = [tokens[i] for i in a.token_idxs]
            print([f"{t.sentence_idx}-{t.idx} {t.text}" for t in anno_tokens])
            ta = [token_annotations[i] for i in a.token_idxs]
            ta_text_list = [a["metadata"]["text"] for a in ta]
            print(ta_text_list)
            print()
            # if ' '.join(ta_text_list) != a.text:
            #     raise Exception("!")


def make_doc_id(p):
    return p.split('/')[-1].replace('.tsv', '')


if __name__ == '__main__':
    main()
