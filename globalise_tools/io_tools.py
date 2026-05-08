import csv
import json
from typing import Any

import orjson

from globalise_tools.logger_tools import log_reading_file, log_writing_file


def read_json(path: str, quiet: bool = False) -> Any:
    if not quiet:
        log_reading_file(path)
    with open(path, 'rb') as f:
        data = orjson.loads(f.read())
    return data


def write_json(path: str, data: Any, quiet: bool = False) -> None:
    if not quiet:
        log_writing_file(path)
    with open(path, mode='w', newline='') as file:
        json.dump(data, file, indent=4)


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
