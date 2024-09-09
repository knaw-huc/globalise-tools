import csv
from dataclasses import dataclass

from loguru import logger


@dataclass
class LangDeduction:
    langs: list[str]
    corrected: bool


def read_lang_deduction_for_page(path: str) -> dict[str, LangDeduction]:
    langs_for_page = {}
    logger.info(f"<= {path}")
    with open(path) as file:
        reader = csv.DictReader(file, delimiter='\t')
        for record in reader:
            lang_deduction = LangDeduction(langs=record['langs'].split(','), corrected=record['corrected'] == "1")
            key = f"NL-HaNA_1.04.02_{record['inv_nr']}_{record['page_no']}"
            langs_for_page[key] = lang_deduction
    return langs_for_page
