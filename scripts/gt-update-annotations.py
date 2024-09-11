#!/usr/bin/env python3
import json

import hydra
from annorepo.client import AnnoRepoClient
from loguru import logger
from omegaconf import DictConfig

import globalise_tools.lang_deduction as ld


@hydra.main(version_base=None)
@logger.catch
def main(cfg: DictConfig) -> None:
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
