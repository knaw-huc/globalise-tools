from enum import Enum

URI_BASE_PATTERN = "https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/"


# see: https://gist.github.com/LvanWissen/736606df05b788aad38e3a74325300c7

class AnnotationPageType(Enum):
    TRANSCRIPTIONS = "transcriptions"
    ENTITIES = "entities"
    EVENTS = "events"


# Concepts

def concept_url(identifier: str) -> str:
    return _base_url("thesaurus", identifier)


# Entities

def inventory_url(identifier: str) -> str:
    return _base_url("inventory", identifier)


def document_url(identifier: str) -> str:
    return _base_url("document", identifier)


def person_url(identifier: str) -> str:
    return _base_url("person", identifier)


def organization_url(identifier: str) -> str:
    return _base_url("organization", identifier)


def polity_url(identifier: str) -> str:
    return _base_url("polity", identifier)


def ship_url(identifier: str) -> str:
    return _base_url("ship", identifier)


def place_url(identifier: str) -> str:
    return _base_url("place", identifier)


# Events
def event_url(identifier: str) -> str:
    return _base_url("event", identifier)


# Annotations and Manifest (IIIF)

def manifest_url(inventory_number: str) -> str:
    return f"https://data.globalise.huygens.knaw.nl/manifests/inventories/{inventory_number}.json"


def manifest_url0(inventory_number: str) -> str:
    return f"{inventory_url(inventory_number)}.manifest"


def canvas_id(inventory_number: str, page_num: int) -> str:
    return f"{manifest_url(inventory_number)}/canvas/p{page_num}"


def canvas_url(identifier: str) -> str:
    return _base_url("canvas", identifier)


def annotation_page_url(ap_type: AnnotationPageType, identifier: str) -> str:
    return _base_url(f"annotations:{ap_type.value}", identifier)


def annotation_url(ap_type: AnnotationPageType, ap_identifier: str, identifier: str) -> str:
    return f"{annotation_page_url(ap_type, ap_identifier)}#{identifier}"


# utility methods
def _base_url(type: str, identifier: str) -> str:
    return f"{URI_BASE_PATTERN}{type}:{identifier}"
