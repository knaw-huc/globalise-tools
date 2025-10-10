#!/usr/bin/env python3
import json
from dataclasses import dataclass

from dataclasses_json import dataclass_json
from loguru import logger
from progressbar import Bar, ETA, Timer, SimpleProgress, ProgressBar


@dataclass_json
@dataclass
class TimeSpan:
    end_of_the_begin: str
    begin_of_the_end: str


widgets = [
    '[',
    SimpleProgress(),
    Bar(marker='\x1b[32m#\x1b[39m'),
    Timer(),
    '|',
    ETA(),
    ']'
]


def as_time_span(dates: list[str]) -> TimeSpan:
    range_limits = set()
    for date_string in dates:
        parts = date_string.split("/")
        for part in parts:
            if len(part) == 4:  # just the year
                range_limits.add(f"{part}-01-01")
                range_limits.add(f"{part}-12-31")
            else:  # full YYYY-MM-DD date
                range_limits.add(part)
    lowest = min(range_limits) + "T00:00:00Z"
    highest = max(range_limits) + "T23:59:59Z"
    return TimeSpan(end_of_the_begin=highest, begin_of_the_end=lowest)


def convert_inventory2dates():
    in_path = "data/inventory2dates.json"
    out_path = "data/inventory2timespan.json"

    logger.info(f"<= {in_path}")
    with open(in_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    inventory2timespan = {}
    with ProgressBar(widgets=widgets, max_value=len(data), redirect_stdout=True) as bar:
        for i, inv_nr in enumerate(data):
            dates = data[inv_nr]
            time_span = as_time_span(dates)
            inventory2timespan[inv_nr] = time_span.__dict__
            # print(inv_nr)
            # print(dates)
            # print(time_span)
            # print()
            bar.update(i)

    logger.info(f"=> {out_path}")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(inventory2timespan, fp=f, indent=2)



def main():
    convert_inventory2dates()


if __name__ == '__main__':
    main()
