#!/usr/bin/env python3
import json
from collections import defaultdict

from loguru import logger

static_file_path = '/Users/bram/workspaces/static-file-server'


def main():
    annotations = load_annotations("out/10060/ner-annotations.json")

    annos_per_canvas = defaultdict(list)
    for a in annotations:
        if type(a["@context"]) is str:
            if len(a["target"]) > 1:
                canvas_id = a["target"][-1]["source"]["id"]
                a.pop("@context")
                annos_per_canvas[canvas_id].append(a)

    manifest_path = f"{static_file_path}/10060.json"
    manifest = load_manifest(manifest_path)
    for canvas in manifest['items']:
        canvas_id = canvas['id']
        canvas_annos = annos_per_canvas[canvas_id]
        if canvas_annos:
            cap = annotation_page(canvas_annos)
            page_id = f"{manifest_path.split('/')[-1].replace('.json', '')}-{canvas_id.split('/')[-1]}"
            annotation_page_path = f"{static_file_path}/{page_id}.json"
            store_annotation_page(annotation_page_path, cap)
            page_url = f"https://brambg.github.io/static-file-server/{page_id}.json"
            canvas["annotations"] = [{'id': page_url, 'type': 'AnnotationPage'}]
    store_manifest(manifest, manifest_path)


def annotation_page(canvas_annotations: list[dict[str, any]]) -> dict[str, any]:
    return {
        "type": "AnnotationPage",
        "items": canvas_annotations
    }


def store_annotation_page(annotation_page_path, cap):
    logger.info(f"=> {annotation_page_path}")
    with open(annotation_page_path, "w") as f:
        json.dump(cap, fp=f)


def store_manifest(manifest, manifest_path):
    logger.info(f"=> {manifest_path}")
    with open(manifest_path, 'w') as f:
        json.dump(manifest, fp=f)


def load_annotations(path: str) -> list[dict[str, any]]:
    logger.info(f"<= {path}")
    with open(path) as f:
        annotations = json.load(f)
    return annotations


def load_manifest(manifest_path):
    logger.info(f"<= {manifest_path}")
    with open(manifest_path) as f:
        manifest = json.load(f)
    return manifest


if __name__ == '__main__':
    main()
