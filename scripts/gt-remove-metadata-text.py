#!/usr/bin/env python3
import json
import sys

from loguru import logger


def remove_text(d: dict[str, any]):
    if 'body' in d and 'metadata' in d['body'] and 'text' in d['body']['metadata']:
        d['body']['metadata'].pop('text')
        if not d['body']['metadata']:
            d['body'].pop('metadata')
    return d


def main(path: str):
    logger.info(f"<= {path}")
    with open(path) as f:
        annotations = json.load(f)
    new_annotations = [remove_text(a) for a in annotations]
    with open(path, 'w') as f:
        json.dump(new_annotations, f)


if __name__ == '__main__':
    main(sys.argv[1])
