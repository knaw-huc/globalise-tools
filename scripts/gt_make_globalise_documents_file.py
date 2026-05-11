#!/usr/bin/env python3
import itertools
import re
import sys
from typing import Any
from xml.etree.ElementTree import Element

from loguru import logger
from lxml import etree

import globalise_tools.io_tools as rw
from globalise_tools.logger_tools import log_reading_file

ns = {"ead": "https://www.nationaalarchief.nl/collectie/ead/ead.dtd"}


class EADParser:
    def __init__(self, path: str):
        self.path = path
        self.data = {}
        self.parsed = False

    def parse(self) -> dict[str, dict[str, Any]]:
        log_reading_file(self.path)
        root = etree.parse(self.path).getroot()
        dsc = root.findall(".//dsc", namespaces=ns)
        for d in dsc:
            self._parse_series(d)
        self.parsed = True
        return self.data

    def _parse_series(self, element: Element) -> None:
        for series_element in element.findall("./c[@level='series']", namespaces=ns):
            series_id = self._series_id(series_element)
            hierarchy = [series_id]
            self._parse_subseries(series_element, hierarchy)
            self._parse_filegrps(series_element, hierarchy)
            self._parse_files(series_element, hierarchy)

    def _parse_subseries(self, element: Element, hierarchy: list[str]) -> None:
        for subseries_element in element.findall("./c[@level='subseries']", namespaces=ns):
            subseries_id = self._series_id(subseries_element)
            new_hierarchy = hierarchy.copy()
            new_hierarchy.append(subseries_id)
            self._parse_subseries(subseries_element, new_hierarchy)
            self._parse_filegrps(subseries_element, new_hierarchy)
            self._parse_files(subseries_element, new_hierarchy)

    def _parse_filegrps(self, element: Element, hierarchy: list[str]) -> None:
        for filegrp in element.findall("./c[@otherlevel='filegrp']", namespaces=ns):
            unitid = self._normalize(filegrp.findall("./did/unitid", namespaces=ns)[0].text)
            unittitle = self._normalize(filegrp.findall("./did/unittitle", namespaces=ns)[0].text)
            filegrp_id = f"{unitid} - {unittitle}"
            new_hierarchy = hierarchy.copy()
            new_hierarchy.append(filegrp_id)
            self._parse_filegrps(filegrp, new_hierarchy)
            self._parse_files(filegrp, new_hierarchy)

    def _parse_files(self, element: Element, hierarchy: list[str]) -> None:
        for f in element.findall("./c[@level='file']", namespaces=ns):
            date = f.findall("./did//unitdate", namespaces=ns)
            date_str: str | None = None
            if date:
                date_str = date[0].get("normal")
            for i in f.findall("./did/unitid[@identifier]", namespaces=ns):
                inv_nr = str(i.text)
                if inv_nr in self.data and self.data[inv_nr]["hierarchy"] != hierarchy:
                    logger.warning(f"overwriting hierarchy for inventory number {inv_nr}")
                data = {"hierarchy": hierarchy}
                if date_str:
                    data["date"] = date_str
                self.data[inv_nr] = data

    def _series_id(self, element: Element) -> str:
        code = str(element.findall("./did/unitid[@type='series_code']", namespaces=ns)[0].text)
        title = self._normalize(element.findall("./did/unittitle", namespaces=ns)[0].text)
        return f"{code} - {title}"

    @staticmethod
    def _debug(e: Element) -> None:
        xml = etree.tostring(e, pretty_print=True, encoding="unicode")
        print(xml, file=sys.stderr)

    @staticmethod
    def _normalize(string: Any) -> str:
        return re.sub(r"\s+", " ", str(string)).strip()


@logger.catch
def main():
    ead_inv_data = EADParser("data/1.04.02.xml").parse()

    records = rw.read_json("data/inventory2dates.json")
    dates4inventory = {r["inventory_number"]: r for r in records}

    text = rw.read_text("data/all-page-ids.lst")
    page_ids = text.splitlines()
    logger.info(f"read {len(page_ids)} page ids")

    groups = itertools.groupby(page_ids, lambda p: "_".join(p.split("_")[:3]))
    documents = []
    for doc_id, page_ids in groups:
        inventory_number = doc_id.split("_")[-1]
        doc = dates4inventory[inventory_number]
        if inventory_number in ead_inv_data:
            ead = ead_inv_data[inventory_number]
            for key in ["date", "hierarchy"]:
                if key in ead:
                    doc[key] = ead[key]
        else:
            logger.warning(f"inventory number {inventory_number} not found in ead xml")
        page_id_list = list(page_ids)
        doc["number_of_pages"] = len(page_id_list)
        doc["page_ids"] = page_id_list
        documents.append(doc)

    logger.info(f"writing {len(documents)} document definitions")
    rw.write_json("data/globalise-documents.json", documents)


if __name__ == '__main__':
    main()
