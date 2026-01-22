import globalise_tools.url_factory as uf
from globalise_tools.url_factory import AnnotationPageType


def test_concept_url():
    assert uf.concept_url("identifier") == \
           'https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/thesaurus:identifier'


def test_inventory_url():
    assert uf.inventory_url("NL-HaNA_1.04.02_3598_0797") == \
           'https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/inventory:NL-HaNA_1.04.02_3598_0797'


def test_document_url():
    assert uf.document_url("identifier") == \
           'https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/document:identifier'


def test_person_url():
    assert uf.person_url("identifier") == \
           'https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/person:identifier'


def test_organization_url():
    assert uf.organization_url('organization_identifier') == \
           'https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/organization:organization_identifier'


def test_polity_url():
    assert uf.polity_url('polity_identifier') == \
           'https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/polity:polity_identifier'


def test_ship_url():
    assert uf.ship_url('ship_identifier') == \
           'https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/ship:ship_identifier'


def test_place_url():
    assert uf.place_url('place_identifier') == \
           'https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/place:place_identifier'


def test_event_url():
    assert uf.event_url('event_identifier') == \
           'https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/event:event_identifier'


# old
def test_manifest_url():
    assert uf.manifest_url('3598') == \
           'https://data.globalise.huygens.knaw.nl/manifests/inventories/3598.json'


# new
def test_manifest_url0():
    assert uf.manifest_url0('3598') == \
           'https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/inventory:3598.manifest.jsonld'


def test_canvas_url():
    assert uf.canvas_url('canvas_identifier') == \
           'https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/canvas:canvas_identifier'


def test_annotation_page_url():
    assert uf.annotation_page_url(AnnotationPageType.TRANSCRIPTIONS, 'NL-HaNA_1.04.02_3598_0797') == \
           'https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/annotations:transcriptions:NL-HaNA_1.04.02_3598_0797.jsonld'
    assert uf.annotation_page_url(AnnotationPageType.ENTITIES, 'NL-HaNA_1.04.02_3598_0798') == \
           'https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/annotations:entities:NL-HaNA_1.04.02_3598_0798.jsonld'
    assert uf.annotation_page_url(AnnotationPageType.EVENTS, 'NL-HaNA_1.04.02_3598_0799') == \
           'https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/annotations:events:NL-HaNA_1.04.02_3598_0799.jsonld'


def test_annotation_url():
    assert uf.annotation_url(AnnotationPageType.TRANSCRIPTIONS, 'NL-HaNA_1.04.02_3598_0796', 'annotation_identifier') == \
           'https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/annotations:transcriptions:NL-HaNA_1.04.02_3598_0796.jsonld#annotation_identifier'
