#!/usr/bin/env python3
import json
import os


def list_web_annotation_files(directory: str):
    all_files = os.listdir(directory)
    return sorted([f'{directory}/{f}' for f in all_files if f.endswith("-web-annotations.json")])


def main():
    files = list_web_annotation_files("out")
    long_word_annotations = []
    joined_word_annotations = []
    for p in files:
        with open(p) as f:
            annotations = json.load(f)
            long_word_annotations.extend([a for a in annotations if is_long_word_annotation(a)])
            joined_word_annotations.extend([a for a in annotations if is_joined_word_annotation(a)])
    for l in sorted(long_word_annotations, key=word_length):
        print(json.dumps(l, indent=2))
    for l in sorted(joined_word_annotations, key=word_length):
        print(json.dumps(l, indent=2))


def word_length(a):
    return len(a["body"]["text"])


def is_long_word_annotation(a):
    return a["body"]["type"] == "px:Word" and len(a["body"]["text"]) > 5


def is_joined_word_annotation(a):
    return a["body"]["type"] == "px:Word" and len([t for t in a["target"] if t["type"] == "Image" and "selector" in t]) > 1


if __name__ == '__main__':
    main()
