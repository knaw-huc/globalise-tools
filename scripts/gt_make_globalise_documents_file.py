#!/usr/bin/env python3
import itertools
import json

from loguru import logger

from globalise_tools.logger_tools import log_reading_file, log_writing_file


@logger.catch
def main():
    path = "data/inventory2dates.json"
    log_reading_file(path)
    with open(path, "r") as f:
        records = json.load(f)
    dates4inventory = {r["inventory_number"]: r for r in records}

    path = "data/all-page-ids.lst"
    log_reading_file(path)
    with open(path, "r") as f:
        page_ids = f.read().splitlines()
        logger.info(f"read {len(page_ids)} page ids")

    groups = itertools.groupby(page_ids, lambda p: "_".join(p.split("_")[:3]))
    documents = []
    for doc_id, page_ids in groups:
        inventory_number = doc_id.split("_")[-1]
        doc = dates4inventory[inventory_number]
        page_id_list = list(page_ids)
        doc["number_of_pages"] = len(page_id_list)
        doc["page_ids"] = page_id_list
        documents.append(doc)

    path = "data/globalise-documents.json"
    logger.info(f"writing {len(documents)} document definitions")
    log_writing_file(path)
    with open(path, "w") as f:
        json.dump(documents, f)


if __name__ == '__main__':
    main()
