#!/usr/bin/env python3
import csv
import json

from loguru import logger

metadata_paths = ["/Users/bram/workspaces/globalise/annotation/2024/document_metadata.csv",
                  "/Users/bram/workspaces/globalise/annotation/2024/document_metadata_esta.csv"]

result_path = "out/results.json"


def read_document_id_idx(result_path: str) -> dict[str, str]:
    logger.info(f"<= {result_path}")
    with open(result_path) as f:
        result = json.load(f)
        return result["document_id_idx"]


def update_record(record: dict[str, str], document_id_idx: dict[str, str]) -> dict[str, str]:
    internal_id = record['internal_id']
    updated_record = dict(record)
    if internal_id in document_id_idx:
        updated_record['document_id'] = document_id_idx[internal_id]
    return updated_record


@logger.catch
def main():
    document_id_idx = read_document_id_idx(result_path)
    for p in metadata_paths:
        logger.info(f"<= {p}")
        updated_records = []
        with open(p) as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames
            for record in reader:
                updated_records.append(update_record(record, document_id_idx))
        logger.info(f"=> {p}")
        with open(p, 'w') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(updated_records)


if __name__ == '__main__':
    main()
