import csv
from dataclasses import dataclass, field

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class DocumentMetadata:
    document_id: str
    internal_id: str
    globalise_id: str
    quality_check: str
    title: str
    year_creation_or_dispatch: str
    inventory_number: str
    folio_or_page: str
    folio_or_page_range: str
    scan_range: str
    scan_start: str
    scan_end: str
    no_of_scans: str
    no_of_pages: str
    GM_id: str
    tanap_id: str
    tanap_description: str
    remarks: str
    marginalia: str
    partOf500_filename: str
    partOf500_folio: str
    esta_voyage_id: str
    esta_subvoyage_id: str
    first_scan_nr: int = field(init=False)
    last_scan_nr: int = field(init=False)
    hana_nr: str = field(init=False)
    external_id: str = field(init=False)
    pagexml_ids: list[str] = field(init=False)

    def __post_init__(self):
        if self.no_of_pages:
            self.no_of_pages = int(self.no_of_pages)
        else:
            self.no_of_pages = 1
        if self.no_of_scans:
            self.no_of_scans = int(self.no_of_scans)
        else:
            self.no_of_scans = 1
        (self.first_scan_nr, self.last_scan_nr) = self._scan_nr_range()
        self.hana_nr = f"NL-HaNA_1.04.02_{self.inventory_number}"
        self.external_id = self._external_id()
        self.pagexml_ids = self._pagexml_ids()

    def _scan_nr_range(self) -> (int, int):
        if '-' in self.scan_range:
            (first_str, last_str) = self.scan_range.split('-')
            first = int(first_str)
            last = int(last_str)
        else:
            first = last = 0
        return first, last

    def _external_id(self) -> str:
        return f"{self.hana_nr}_{self.first_scan_nr:04d}-{self.last_scan_nr:04d}"

    def _pagexml_ids(self) -> list[str]:
        return [f"{self.hana_nr}_{n:04d}" for n in range(self.first_scan_nr, self.last_scan_nr + 1)]


def read_document_metadata(selection_file: str) -> list[DocumentMetadata]:
    with open(selection_file, encoding='utf8') as f:
        f.readline()
        reader = csv.DictReader(f, fieldnames=[
            "document_id", "internal_id", "globalise_id", "quality_check", "title", "year_creation_or_dispatch",
            "inventory_number",
            "folio_or_page", "folio_or_page_range", "scan_range", "scan_start", "scan_end", "no_of_scans",
            "no_of_pages", "GM_id", "tanap_id", "tanap_description", "remarks", "marginalia",
            "partOf500_filename", "partOf500_folio"])
        all_metadata = [DocumentMetadata.from_dict(row) for row in reader]
    return all_metadata
