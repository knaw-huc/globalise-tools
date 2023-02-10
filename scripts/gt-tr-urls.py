#!/usr/bin/env python3
import csv

from loguru import logger


@logger.catch
def main():
    tr_version_csv = "data/tr-versions.csv"
    base_url = "https://globalise.tt.di.huc.knaw.nl/textrepo"
    with open(tr_version_csv) as f:
        reader = csv.DictReader(f)
        tr_docs = [r for r in reader]

    for d in tr_docs:
        external_id = d['external_id']
        print(f"{external_id}:")

        task_url = f"{base_url}/task/find/{external_id}/file/contents?type=conll"
        print(f"\t{task_url}")

        conll_version = d['conll_version']
        conll_url = f"{base_url}/rest/versions/{conll_version}/contents"
        print(f"\t{conll_url}")

        segments_url = f"{base_url}/view/versions/{d['segmented_version']}/segments/index/10/100"
        print(f"\t{segments_url}")

        print(f"{external_id};{conll_version};{conll_url}")


if __name__ == '__main__':
    main()
