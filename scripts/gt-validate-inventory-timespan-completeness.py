#!/usr/bin/env python3

from gt_ner_xmi_to_wa import load_timespan_dict


def load_inv_nrs():
    path = "data/inventory-numbers.lst"
    with open(path) as f:
        return [l.strip() for l in f.readlines()]


def main() -> None:
    inv_nrs = load_inv_nrs()
    timezones = load_timespan_dict()
    available = timezones.keys()
    missing = set(inv_nrs) - available
    if len(missing) > 0:
        print(f"{len(missing)}/{len(inv_nrs)} Missing timespan:")
        for n in sorted(missing):
            print(f" {n}")


if __name__ == '__main__':
    main()
