#!/usr/bin/env python3
import json
import timeit

import orjson

json_in_path = "../work/1053/ner-annotations.json"
json_out_path = "../work/1053/ner-annotations.json.bak"


def main():
    obj = json_load()
    num = 10
    for d in [json_load, orjson_load]:
        print(f"Running {d} {num} times ...")
        execution_time = timeit.timeit(lambda: d(), number=num)
        print(f"Execution time:")
        print(f"    total: {execution_time} seconds")
        print(f"  average: {execution_time / num} seconds")
        print()

    for d in [json_dump, json_dump_with_indent, orjson_dump]:
        print(f"Running {d} {num} times ...")
        execution_time = timeit.timeit(lambda: d(obj), number=num)
        print(f"Execution time:")
        print(f"    total: {execution_time} seconds")
        print(f"  average: {execution_time / num} seconds")
        print()


def json_load():
    with open(json_in_path) as f:
        o = json.load(f)
    return o


def orjson_load():
    with open(json_in_path) as f:
        s = f.read()
        o = orjson.loads(s)


def json_dump(o):
    with open(json_out_path, 'w') as f:
        json.dump(o, f, ensure_ascii=False)


def json_dump_with_indent(o):
    with open(json_out_path, 'w') as f:
        json.dump(o, f, indent=4, ensure_ascii=False)


def orjson_dump(o):
    with open(json_out_path, 'wb') as f:
        f.write(orjson.dumps(o))


if __name__ == '__main__':
    main()
