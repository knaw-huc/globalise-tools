import uuid
from dataclasses import dataclass, field
from datetime import datetime
from json import JSONEncoder
from typing import Dict, Any, List

from dataclasses_json import dataclass_json
from pagexml.model.physical_document_model import Coords

import globalise_tools.tools as gt


@dataclass
class Document:
    id: str
    tanap_id: str
    index_nr: str
    archief: str
    deel: str
    folio_begin: str
    folio_eind: str
    scan_begin: int
    scan_eind: int
    gescanned: str
    rgp_deel: str
    rgp_start: str
    jaar: str
    beschrijving: str
    datum: str
    datum_numeriek: str
    link_naar_eerste_scan: str
    bestandsnaam_van_eerste_scan: str
    link_naar_laatste_scan: str
    bestandsnaam_van_laatste_scan: str
    htr_van_ijsberg_beschikbaar: bool

    @staticmethod
    def from_dict(d: Dict[str, str]) -> 'Document':
        return Document(
            id=d["ID"],
            tanap_id=d["TANAP ID"],
            index_nr=d["Indexnr"],
            archief='Zeeland' if d['Archief Amsterdam of Zeeland?'] == 'Z' else 'Amsterdam',
            deel=d['Deel'],
            folio_begin=d['Folio-begin'],
            folio_eind=d['Folio-eind'],
            scan_begin=as_int(d['Scan-begin']),
            scan_eind=as_int(d['Scan-Eind']),
            gescanned=d['Enkel gescanned of dubbel?'],
            rgp_deel=d['RGP Deel'],
            rgp_start=d['RGP START'],
            jaar=d['Jaar'],
            beschrijving=d['Beschrijving'],
            datum=d['Datum'],
            datum_numeriek=d['Datum (nummeriek)'],
            link_naar_eerste_scan=d['LINK naar eerste scan'],
            bestandsnaam_van_eerste_scan=d['Bestandsnaam van eerste scan'],
            link_naar_laatste_scan=d['LINK naar laatste scan'],
            bestandsnaam_van_laatste_scan=d['Bestandsnaam van laatste scan'],
            htr_van_ijsberg_beschikbaar=(d['HTR van IJsberg beschikbaar?'].lower() == 'true')
        )

    def scan_ids(self) -> List[str]:
        base = f"NL-HaNA_1.04.02_{self.index_nr}"
        return [f"{base}_{s:04d}" for s in range(self.scan_begin, self.scan_eind + 1)]

    def hana_id(self) -> str:
        return f"NL-HaNA_1.04.02_{self.index_nr}_{self.scan_begin:04d}-{self.scan_eind:04d}"

    def has_scans(self) -> bool:
        return self.scan_begin > 0


def as_int(string: str) -> int:
    return int(string) if string.isdigit() else 0


@dataclass
class WebAnnotation:
    body: Dict[str, Any]
    target: Any
    custom: dict[str, Any] = field(default_factory=dict, hash=False)

    def wrapped(self):
        anno_uuid = uuid.uuid4()
        dict = {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "id": f"urn:globalise:annotation:{anno_uuid}",
            "type": "Annotation",
            "motivation": "classifying",
            "generated": datetime.today().isoformat(),  # use last-modified from pagexml for px: types
            "generator": {  # use creator metadata from pagexml for px: types
                "id": "https://github.com/knaw-huc/loghi-htr",
                "type": "Software",
                "name": "Loghi"
            },
            "body": self.body,
            "target": self.target
        }
        if self.custom:
            dict.update(self.custom)
        return dict


@dataclass
class TRVersions:
    txt: str
    segmented: str
    conll: str


@dataclass_json
@dataclass
class GTToken:
    text: str
    text_with_ws: str
    offset: int


class AnnotationEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, gt.Annotation) \
                or isinstance(obj, gt.PXTextRegion) \
                or isinstance(obj, gt.PXTextLine) \
                or isinstance(obj, GTToken):
            return obj.to_dict()
        elif isinstance(obj, WebAnnotation):
            return obj.wrapped()
        elif isinstance(obj, Coords):
            return obj.points
