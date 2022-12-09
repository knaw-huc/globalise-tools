#!/usr/bin/env python3
import itertools
import json
import os
import random
from typing import List, Dict


def list_web_annotation_files(directory: str):
    all_files = os.listdir(directory)
    return sorted([f'{directory}/{f}' for f in all_files if f.endswith("-web-annotations.json")])


def main():
    files = list_web_annotation_files("out")
    annotations = []
    for p in files:
        with open(p) as f:
            annotations.extend(json.load(f))

    # show_long_word_annotations(annotations)

    # show_joined_word_annotations(annotations)

    show_random_annotation_of_each_type(annotations)


def show_joined_word_annotations(annotations):
    joined_word_annotations = [a for a in annotations if is_joined_word_annotation(a)]
    for l in sorted(joined_word_annotations, key=word_length):
        print(json.dumps(l, indent=2))


def show_long_word_annotations(annotations):
    long_word_annotations = [a for a in annotations if is_long_word_annotation(a)]
    for l in sorted(long_word_annotations, key=word_length):
        print(json.dumps(l, indent=2))


def show_random_annotation_of_each_type(annotations):
    random_annotations = []
    annotations.sort(key=body_type)
    grouped_by_type = itertools.groupby(annotations, key=body_type)
    for atype, group in grouped_by_type:
        # ic(atype)
        random_annotations.append(random.choice(list(group)))
    joined_words = [a for a in annotations if is_joined_word_annotation(a)]
    random_annotations.append(random.choice(joined_words))
    print(json.dumps(sorted(random_annotations, key=body_type), indent=2))


def body_type(annotation):
    return annotation["body"]["type"]


def word_length(a):
    return len(a["body"]["text"])


def is_long_word_annotation(a):
    return a["body"]["type"] == "tt:Word" and len(a["body"]["text"]) > 5


def is_fragment_selector_target(target: dict) -> bool:
    return target["type"] == "Image" \
        and "selector" in target \
        and has_fragment_selector(target["selector"])


def has_fragment_selector(selectors: List[Dict[str, str]]) -> bool:
    fragment_selectors = [s for s in selectors if s["type"] == "FragmentSelector"]
    return len(fragment_selectors) > 0


def is_joined_word_annotation(a):
    fragment_selector_targets = [t for t in a["target"] if is_fragment_selector_target(t)]
    return a["body"]["type"] == "tt:Word" \
        and len(fragment_selector_targets) > 0 \
        and len(fragment_selector_targets[0]['selector']) > 2


if __name__ == '__main__':
    main()
