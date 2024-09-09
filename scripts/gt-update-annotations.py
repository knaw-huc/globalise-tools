#!/usr/bin/env python3
import hydra
from annorepo.client import AnnoRepoClient
from loguru import logger
from omegaconf import DictConfig

import globalise_tools.lang_deduction as ld


@hydra.main(version_base=None)
@logger.catch
def main(cfg: DictConfig) -> None:
    lang_deduction_for_page = ld.read_lang_deduction_for_page(cfg.automated_page_langs_file)
    ar = AnnoRepoClient(cfg.annorepo.base_url, api_key=cfg.annorepo.api_key)
    ca = ar.container_adapter(cfg.annorepo.container_name)
    annotation_iterator = ca.read_annotations()
    for anno in annotation_iterator:
        if anno["body"]["type"] == "px:Page":
            anno_url = anno["id"]
            anno_name = anno_url.split("/")[-1]
            anno_result = ca.read_annotation(anno_name)
            etag = anno_result.etag
            anno = anno_result.annotation

            page_id = anno["body"]["metadata"]["document"]
            lang_deduction = lang_deduction_for_page[page_id]
            # update the annotation dict
            anno["body"]["metadata"]["lang"] = lang_deduction.langs
            anno["body"]["metadata"]["langCorrected"] = lang_deduction.corrected
            logger.info(f"updating annotation {anno_url}")
            ca.update_annotation(anno_name, etag, anno)
