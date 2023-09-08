#!/usr/bin/env python3
import json

from loguru import logger


@logger.catch
def main() -> None:
    import pathlib
    inventories_path = pathlib.Path("/Users/bram/workspaces/globalise/manifests/inventories")
    scan_url_mapping = {}
    manifest_paths = list(inventories_path.glob("*.json"))
    manifest_paths.sort()
    total = len(manifest_paths)
    for i, p in enumerate(manifest_paths):
        logger.info(f"<= {p} [{i + 1}/{total}]")
        with open(p) as f:
            manifest = json.load(f)
            mapping = {i['label']['en'][0]: i['items'][0]['items'][0]['body']['id'].replace('srv?IIIF=', '')
                       for i in manifest['items']}
            scan_url_mapping.update(mapping)
    mapping_json_path = "data/scan_url_mapping.json"
    logger.info(f"=> {mapping_json_path}")
    with open(mapping_json_path, "w") as f:
        json.dump(scan_url_mapping, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    main()
