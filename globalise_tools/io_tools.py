import csv
import json
from json import JSONEncoder
from typing import Any

import orjson
import requests

from globalise_tools.logger_tools import log_reading_file, log_writing_file


def read_json(path: str, quiet: bool = False) -> Any:
    if not quiet:
        log_reading_file(path)
    with open(path, 'rb') as f:
        data = orjson.loads(f.read())
    return data


def get_json(url: str, quiet: bool = False) -> Any:
    if not quiet:
        log_reading_file(url)
    s = requests.Session()
    s.trust_env = False
    result = s.get(url)
    if result.status_code != 200:
        return None
    json_data = result.text
    data = orjson.loads(json_data)
    return data


def write_json(path: str, data: Any, clean_nones: bool = True, quiet: bool = False,
               encoder: type[JSONEncoder] = JSONEncoder) -> None:
    if not quiet:
        log_writing_file(path)
    if clean_nones:
        data = _clean_nones(data)
    if encoder != JSONEncoder:
        with open(path, mode='w', newline='') as file:
            json.dump(data, file, indent=4, ensure_ascii=False, cls=encoder)
    else:
        with open(path, "wb") as f:
            f.write(orjson.dumps(data))


def read_text(path: str, quiet: bool = False) -> str:
    if not quiet:
        log_reading_file(path)
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    return text


def write_text(path: str, text: str, quiet: bool = False) -> None:
    if not quiet:
        log_writing_file(path)
    with open(path, mode='w', newline='') as file:
        file.write(text)


def write_tsv(path: str, headers: list[str], records: list[Any], quiet: bool = False) -> None:
    if not quiet:
        log_writing_file(path)
    with open(path, mode='w', newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        writer.writerow(headers)
        writer.writerows(records)


def write_csv(path: str, headers: list[str], records: list[Any], quiet: bool = False) -> None:
    if not quiet:
        log_writing_file(path)
    with open(path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(records)


def _clean_nones(value: Any) -> Any:
    """
    Recursively remove all None values from dictionaries and lists, and returns
    the result as a new dictionary or list.
    source: https://stackoverflow.com/questions/4255400/exclude-empty-null-values-from-json-serialization
    """
    if isinstance(value, list):
        return [_clean_nones(x) for x in value if x is not None]
    elif isinstance(value, dict):
        return {
            key: _clean_nones(val)
            for key, val in value.items()
            if val is not None
        }
    else:
        return value
