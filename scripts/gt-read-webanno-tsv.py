#!/usr/bin/env python3
import glob
from typing import List

from icecream import ic

from globalise_tools.webanno_tsv_tools import process_webanno_tsv_file2

data_dir = "data/inception_output"


def web_anno_file_paths(folder: str) -> List[str]:
    return glob.glob(f"{folder}/*.tsv")


def main():
    for p in web_anno_file_paths(data_dir):
        ic(p)
        annotations = process_webanno_tsv_file2(p)

        selection = [a for a in annotations if len(a.layers) > 1]
        ic(selection)

        for a in [a for a in annotations if
                  a.layers[0].label == "de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity"]:
            print(a.text)
            print(a.layers[0].elements[0].fields)
            print([f"{t.sentence_idx}-{t.idx}" for t in a.tokens])
            print()


if __name__ == '__main__':
    main()
