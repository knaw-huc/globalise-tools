#!/usr/bin/env python3
import glob
import os

from loguru import logger

from globalise_tools.tools import inv_nr_sort_key


def generate_manifest_list() -> None:
    inventory_paths = sorted(glob.glob("/Users/bram/workspaces/static-file-server/globalise/*"), key=inv_nr_sort_key)
    inv_nums = [path.split('/')[-1] for path in inventory_paths]
    manifest_uris = [f"https://globalise-mirador.tt.di.huc.knaw.nl/globalise/{inv_nr}/{inv_nr}.json"
                     for inv_nr in inv_nums
                     if os.path.isfile(f"/Users/bram/workspaces/static-file-server/globalise/{inv_nr}/{inv_nr}.json")]
    print(f"/Users/bram/workspaces/static-file-server/globalise/{inv_nums[0]}/{inv_nums[0]}.json")
    out_path = "/Users/bram/workspaces/static-file-server/manifests.lst"
    logger.info(f"=> {out_path}")
    with open(out_path, 'w') as f:
        for m in manifest_uris:
            f.write(f'{{manifestId:"{m}"}},\n')


@logger.catch
def main() -> None:
    generate_manifest_list()


if __name__ == '__main__':
    main()
