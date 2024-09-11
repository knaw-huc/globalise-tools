#!/usr/bin/env python3
import json
import os.path
from dataclasses import dataclass, field

import hydra
from annorepo.client import AnnoRepoClient
from dataclasses_json import dataclass_json
from loguru import logger
from omegaconf import DictConfig

import globalise_tools.lang_deduction as ld

page_id_field = "body.metadata.document"

result_path = "out/gt-update-annnotations-missing-lang-detection.json"


@dataclass_json
@dataclass
class ProjectResults:
    pages_without_language_detection: list[str] = field(default_factory=list)
    pages_processed: set[str] = field(default_factory=set)


@hydra.main(version_base=None)
@logger.catch
def main(cfg: DictConfig) -> None:
    lang_deduction_for_page = ld.read_lang_deduction_for_page(cfg.automated_page_langs_file)
    ar = AnnoRepoClient(cfg.annorepo.base_uri, api_key=cfg.annorepo.api_key)
    ca = ar.container_adapter(cfg.annorepo.container_name)
    project_results = load_project_results()
    page_ids = lang_deduction_for_page.keys()

    indexes = ca.read_indexes()
    if page_id_field not in [i['field'] for i in indexes]:
        logger.info(f"indexing {page_id_field}")
        ca.create_index(field=page_id_field, index_type="hashed")

    unprocessed_page_ids = sorted(page_ids - project_results.pages_processed)
    total = len(unprocessed_page_ids)
    for i, page_id in enumerate(unprocessed_page_ids):
        logger.info(f"examining page {page_id} ({i + 1}/{total})")
        search_id = ca.create_search({'body.metadata.document': page_id})
        for anno in ca.read_search_result_annotations(search_id.id):
            if "lang" not in anno["body"]["metadata"]:
                anno_url = anno["id"]
                anno_name = anno_url.split("/")[-1]
                anno_result = ca.read_annotation(anno_name)
                etag = anno_result.etag
                anno = anno_result.annotation
                lang_deduction = lang_deduction_for_page[page_id]
                # update the annotation dict
                anno["body"]["metadata"]["lang"] = lang_deduction.langs
                anno["body"]["metadata"]["langCorrected"] = lang_deduction.corrected
                logger.info(f"updating annotation {anno_url}")
                ca.update_annotation(anno_name, etag, anno)
            project_results.pages_processed.add(page_id)
            store_project_results(project_results)


def load_project_results() -> ProjectResults:
    if os.path.exists(result_path):
        logger.info(f"<= {result_path}")
        with open(result_path) as f:
            result_json = f.read()
            return ProjectResults.from_json(result_json)
    else:
        return ProjectResults()


def store_project_results(project_results):
    if project_results:
        logger.info(f"=> {result_path}")
        with open(result_path, "w") as f:
            f.write(project_results.to_json())
        # print_missing_lang_detection(cfg, pages_missing_in_lang_detection)


def main0(cfg: DictConfig) -> None:
    lang_deduction_for_page = ld.read_lang_deduction_for_page(cfg.automated_page_langs_file)
    ar = AnnoRepoClient(cfg.annorepo.base_uri, api_key=cfg.annorepo.api_key)
    ca = ar.container_adapter(cfg.annorepo.container_name)
    pages_missing_in_lang_detection = []
    for anno in ca.read_annotations():
        if anno["body"]["type"] == "px:Page":
            anno_url = anno["id"]
            anno_name = anno_url.split("/")[-1]
            page_id = anno["body"]["metadata"]["document"]
            if page_id in lang_deduction_for_page:
                if "lang" not in anno["body"]["metadata"]:
                    anno_result = ca.read_annotation(anno_name)
                    etag = anno_result.etag
                    anno = anno_result.annotation
                    lang_deduction = lang_deduction_for_page[page_id]
                    # update the annotation dict
                    anno["body"]["metadata"]["lang"] = lang_deduction.langs
                    anno["body"]["metadata"]["langCorrected"] = lang_deduction.corrected
                    logger.info(f"updating annotation {anno_url}")
                    ca.update_annotation(anno_name, etag, anno)
            else:
                logger.warning(f"no language detection found for page {page_id} / {anno['id']}")
                pages_missing_in_lang_detection.append(page_id)
    if pages_missing_in_lang_detection:
        path = "out/gt-update-annnotations-missing-lang-detection.json"
        logger.info(f"=> {path}")
        with open(path) as f:
            json.dump(pages_missing_in_lang_detection, fp=f, indent=4)
        # print_missing_lang_detection(cfg, pages_missing_in_lang_detection)


def print_missing_lang_detection(cfg, pages_missing_in_lang_detection):
    print(f"Pages missing in {cfg.automated_page_langs_file} :")
    for page_id in pages_missing_in_lang_detection:
        parts = page_id.split('_')
        inv_nr = parts[-2]
        page_no = parts[-1]
        print(f"{inv_nr}\t{page_no}")


if __name__ == '__main__':
    main()
