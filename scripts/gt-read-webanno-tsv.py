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
        ic(p)
        doc_id = p.split('/')[-1].replace('.tsv', '')
        word_annotations, token_annotations = load_word_and_token_annotations(doc_id)
        tokens, annotations = process_webanno_tsv_file2(p)

        selection = [a for a in annotations if len(a.layers) > 1]
        ic(selection)

        for a in [a for a in annotations if
                  a.layers[0].label == "de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity"]:
            print(a.text)
            print(a.layers[0].elements[0].fields)
            anno_tokens = [tokens[i] for i in a.token_idxs]
            print([f"{t.sentence_idx}-{t.idx} {t.text}" for t in anno_tokens])
            ta = [token_annotations[i] for i in a.token_idxs]
            ta_text_list = [a["metadata"]["text"] for a in ta]
            print(ta_text_list)
            print()
            if ' '.join(ta_text_list) != a.text:
                raise Exception("!")


if __name__ == '__main__':
    main()
