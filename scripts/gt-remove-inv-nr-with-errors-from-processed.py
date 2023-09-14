#!/usr/bin/env python3
import json


def main():
    with open("out/processed.json") as f:
        processed = set(json.load(f))

    path = "out/results.json"
    with open(path) as f:
        results = json.load(f)

    for id in results.keys():
        if results[id]['errors']:
            processed.discard(id)

    path = "out/processed.json"
    with open(path,'w') as f:
        json.dump(list(processed), f)


if __name__ == '__main__':
    main()
