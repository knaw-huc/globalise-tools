#!/usr/bin/env python3
import csv
import itertools
import json

from loguru import logger

external_id_path = "data/external_ids.csv"
documents_path = "data/pagexml_map.json"


@logger.catch
def main() -> None:
    logger.info(f"<= {external_id_path}")
    with open(external_id_path) as f:
        reader = csv.DictReader(f)
        external_ids = [r['external_id'] for r in reader]
    logger.info(f"{len(external_ids)} external ids loaded")
    grouped = itertools.groupby(external_ids, key=lambda x: x.split('_')[-2])
    page_ids_per_inv_nr = {}
    for inventory_number, page_ids in grouped:
        page_ids_per_inv_nr[inventory_number] = [pi for pi in page_ids]

    logger.info(f"=> {documents_path}")
    with open(documents_path, "w") as f:
        json.dump(page_ids_per_inv_nr, f)


if __name__ == '__main__':
    main()
