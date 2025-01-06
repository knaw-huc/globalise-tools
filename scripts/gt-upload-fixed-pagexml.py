#!/usr/bin/env python3
import os

import hydra
from icecream import ic
from loguru import logger
from omegaconf import DictConfig
from textrepo.client import TextRepoClient

from globalise_tools.document_metadata import read_document_selection


@hydra.main(version_base=None)
@logger.catch
def main(cfg: DictConfig):
    metadata = read_document_selection(cfg.selection_files)
    quality_checked_metadata = [m for m in metadata if record_passes_quality_check(m)]
    textrepo_client = TextRepoClient(cfg.textrepo.base_uri, api_key=cfg.textrepo.api_key, verbose=False)
    with textrepo_client as trc:
        for pagexml_ids in [dm.pagexml_ids for dm in quality_checked_metadata]:
            for external_id in pagexml_ids:
                fixed_pagexml_path = get_fixed_pagexml_path(external_id)
                if os.path.exists(fixed_pagexml_path):
                    with open(fixed_pagexml_path) as f:
                        fixed_content = f.read()
                    version_identifier = trc.import_version(
                        external_id=external_id,
                        type_name="pagexml",
                        contents=fixed_content,
                        allow_new_document=False,
                        as_latest_version=True
                    )
                ic(version_identifier)


acceptable_quality_codes = {'3.1.1', '3.1.2', '3.2', 'TRUE'}


def record_passes_quality_check(m):
    checks = m.quality_check.split(' + ')
    disqualifying_checks = set(checks) - acceptable_quality_codes
    return not disqualifying_checks and not m.document_id


def get_fixed_pagexml_path(external_id: str) -> str:
    return f"/Users/bram/workspaces/globalise/globalise-tools/out-local/fixed-pagexml/{external_id}.xml"


if __name__ == '__main__':
    main()
