import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from hashlib import _Hash
from json import JSONEncoder
from typing import Optional

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
    def from_dict(d: dict[str, str]) -> 'Document':
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

    def scan_ids(self) -> list[str]:
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
    body: dict[str, any]
    target: any
    custom: dict[str, any] = field(default_factory=dict, hash=False)

    def wrapped(self):
        anno_uuid = uuid.uuid4()
        anno_dict = {
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
            anno_dict.update(self.custom)
        return anno_dict


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


@dataclass_json
@dataclass
class ScanCoords:
    iiif_base_uri: str
    canvas_id: str
    coords: Coords


class AnnotationEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, gt.Annotation) \
                or isinstance(obj, gt.PXTextRegion) \
                or isinstance(obj, gt.PXTextLine) \
                or isinstance(obj, ScanCoords) \
                or isinstance(obj, GTToken):
            return obj.to_dict()
        elif isinstance(obj, WebAnnotation):
            return obj.wrapped()
        elif isinstance(obj, Coords):
            return obj.points


CAS_SENTENCE = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence"
CAS_TOKEN = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token"
CAS_PARAGRAPH = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Paragraph"
CAS_MARGINALIUM = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Paragraph"  # TODO: find a better fit
CAS_HEADER = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Heading"


@dataclass
class SimpleAnnotation:
    type: str
    first_anchor: int
    last_anchor: int
    text: str
    coords: Optional[Coords]
    metadata: dict[str, any] = field(default_factory=dict, hash=False)


@dataclass_json
@dataclass
class DocumentMetadata:
    inventory_number: str
    scan_range: str
    scan_start: str
    scan_end: str
    no_of_scans: int
    first_scan_nr: int = field(init=False)
    last_scan_nr: int = field(init=False)
    nl_hana_nr: str = field(init=False)
    external_id: str = field(init=False)
    pagexml_ids: list[str] = field(init=False)

    def __post_init__(self):
        # self.no_of_pages = int(self.no_of_pages)
        self.no_of_scans = int(self.no_of_scans)
        (self.first_scan_nr, self.last_scan_nr) = self._scan_nr_range()
        self.nl_hana_nr = f"NL-HaNA_1.04.02_{self.inventory_number}"
        self.external_id = self._external_id()
        self.pagexml_ids = self._pagexml_ids()

    def _scan_nr_range(self) -> (int, int):
        (first_str, last_str) = self.scan_range.split('-')
        first = int(first_str)
        last = int(last_str)
        return first, last

    def _external_id(self) -> str:
        return f"{self.nl_hana_nr}_{self.first_scan_nr:04d}-{self.last_scan_nr:04d}"

    def _pagexml_ids(self) -> list[str]:
        return [f"{self.nl_hana_nr}_{n:04d}" for n in range(self.first_scan_nr, self.last_scan_nr + 1)]


@dataclass_json
@dataclass
class DocumentMetadata2:
    inventory_number: str
    pagexml_ids: list[str]
    first_scan_nr: int = field(init=False)
    last_scan_nr: int = field(init=False)
    no_of_scans: int = field(init=False)
    nl_hana_nr: str = field(init=False)
    scan_range: str = field(init=False)
    scan_start: str = field(init=False)
    scan_end: str = field(init=False)
    external_id: str = field(init=False)

    def __post_init__(self):
        self.no_of_scans = len(self.pagexml_ids)
        self.nl_hana_nr = f"NL-HaNA_1.04.02_{self.inventory_number}"
        self.scan_start = self.pagexml_ids[0].split('_')[-1]
        self.scan_end = self.pagexml_ids[-1].split('_')[-1]
        self.first_scan_nr = int(self.scan_start)
        self.last_scan_nr = int(self.scan_end)
        self.external_id = self._external_id()
        self.scan_range = f"{self.first_scan_nr}-{self.last_scan_nr}"

    def _external_id(self) -> str:
        return f"{self.nl_hana_nr}_{self.first_scan_nr:04d}-{self.last_scan_nr:04d}"


@dataclass
class LogicalAnchorRange:
    begin_logical_anchor: int
    begin_char_offset: int
    end_logical_anchor: int
    end_char_offset_exclusive: int


@dataclass
class TextData:
    plain_text_source: str
    plain_text_md5: _Hash
    text_intervals: list


class SegmentedTextType(Enum):
    PHYSICAL = 1,
    LOGICAL = 2


@dataclass
class ImageData:
    canvas_id: str
    iiif_base_uri: str
    manifest_uri: str
    xywh: str


NER_DATA_DICT = {
    'CMTY_NAME': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/CMTY_NAME',
        'label': 'Name of Commodity',
        'entity_type': 'urn:globalise:entityType:Commodity'
    },
    'CMTY_QUAL': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/CMTY_QUAL',
        'label': 'Commodity qualifier: colors, processing',
        'entity_type': 'urn:globalise:entityType:CommodityQualifier'
    },
    'CMTY_QUANT': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/CMTY_QUANT',
        'label': 'Quantity',
        'entity_type': 'urn:globalise:entityType:CommodityQuantity'
    },
    'DATE': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/DATE',
        'label': 'Date',
        'entity_type': 'urn:globalise:entityType:Date'
    },
    'DOC': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/DOC',
        'label': 'Document',
        'entity_type': 'urn:globalise:entityType:Document'
    },
    'ETH_REL': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/ETH_REL',
        'label': 'Ethno-religious appelation or attribute, not derived from location name',
        'entity_type': 'urn:globalise:entityType:EthnoReligiousAppelation'
    },
    'LOC_ADJ': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/LOC_ADJ',
        'label': 'Derived (adjectival) form of location name',
        'entity_type': 'urn:globalise:entityType:Location'
    },
    'LOC_NAME': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/LOC_NAME',
        'label': 'Name of Location',
        'entity_type': 'urn:globalise:entityType:Location'
    },
    'ORG': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/ORG',
        'label': 'Organisation name',
        'entity_type': 'urn:globalise:entityType:Organisation'
    },
    'PER_ATTR': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/PER_ATTR',
        'label': 'Other persons attributes (than PER or STATUS)',
        'entity_type': 'urn:globalise:entityType:PersonAttribute'
    },
    'PER_NAME': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/PER_NAME',
        'label': 'Name of Person',
        'entity_type': 'urn:globalise:entityType:Person'
    },
    'PRF': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/PRF',
        'label': 'Profession, title',
        'entity_type': 'urn:globalise:entityType:Profession'
    },
    'SHIP': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/SHIP',
        'label': 'Ship name',
        'entity_type': 'urn:globalise:entityType:Ship'
    },
    'SHIP_TYPE': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/SHIP_TYPE',
        'label': 'Ship type',
        'entity_type': 'urn:globalise:entityType:Ship'
    },
    'STATUS': {
        'uri': 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner/STATUS',
        'label': '(Civic) status',
        'entity_type': 'urn:globalise:entityType:CivicStatus'
    }
}
