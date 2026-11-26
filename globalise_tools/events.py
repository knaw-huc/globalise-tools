from dataclasses import dataclass
from typing import Optional

time_roles = ["Time"]
actor_roles = ["Agent", "AgentPatient", "Benefactive", "Cargo", "Instrument", "Patient"]
place_roles = ["Location", "Path", "Source", "Target"]

NAMED_ENTITY_LAYER_NAME = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity"
EVENT_LAYER_NAME = "webanno.custom.SemPredGLOB"

ENTITIES = {
    "CIV": "Civic/legal mention",
    "CMTY": "Commodity",
    "CMTY_NAME": "Commodity name",
    "CMTY_QUANT": "Commodity quantity",
    "CMTY_QUAL": "Commodity qualifier, if appears to be relevant for subclassification of commodity",
    "DATE": "Date",
    "DOC": "Document",
    "DYN": "Dynasty",
    "ETH_REL": "Ethno-religious/location-based individual",
    "ERL": "Ethno-religious/location-based individual",
    "ERL_QUAL": "Ethno-religious/location-based qualifier",
    "LOC": "Location",
    "LOC_ADJ": "Location adjective",
    "LOC_NAME": "Location name",
    "MES": "Measure",
    "MES_CUR": "Currency (measure)",
    "NUM": "Numerical (exact) quantity",
    "ORG": "Named organisation",
    "PER": "Person",
    "PER_ATTR": "Person attribute",
    "PER_NAME": "Person name",
    "POL": "Politie",
    "POL_LOC": "Politie+location",
    "PRF": "Profession",
    "RNK": "Rank / title",
    "SHIP": "Ship name",
    "SHIP_TYPE": "ship type",
    "STATUS": "status",
    "TIME_DATE": "Date (specific point in time)",
    "TIME_DUR": "Duration",
    "TIME_REL": "Time relation marker",
    "UNFREE": "Slaves en related terms"
}

ner_base = "https://id.globalise.nl/hdl:20.500.14722/thesaurus"
prefix = 'urn:example:globalise:entityType'


@dataclass
class NerData:
    id: str
    uri: str
    label: str
    entity_type: str
    body_type: str
    thesaurus_label: str
    classificatory_subject: str
    classificatory_subject: Optional[str] = None
    appellative_subject: Optional[str] = None


# from https://github.com/globalise-huygens/glob-portal-infomodel/issues/83
THESAURUS_LABEL_TO_URI = {
    "Person": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:c207dd28-0b00-44b0-be2c-c810ab55fdd1",
    "Place": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:179d998f-e0aa-41b7-ac8b-437c21d2d6de",
    "Polity": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:b18a60bb-184b-4406-9f98-ba8590b4c696",
    "Ship": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:6a88e519-f72d-4d85-8dce-13675a685048",
    "Organisation": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:9046bc09-7019-4afb-9edd-7258245fcb42",
    "Commodity": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:c9ab191a-f147-4e6d-aad0-cfef646f9278",
    "Unit": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:958ac1ab-945b-45e6-ac01-07830f6eb750",
    "Document": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:c05a9151-050e-4d47-85a8-9f0758b7556c",
    "Date": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:a0bdd099-e91e-430b-b035-8e22d37e818f",
    "Qualifier": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:a3e3f6d4-f90a-4a3d-bd32-dec4ca79e713",
    "Exchange Unit": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:958ac1ab-945b-45e6-ac01-07830f6eb750"
}

# https://github.com/globalise-huygens/glob-portal-infomodel/issues/82#issuecomment-6948973262
EVENT_TO_CATEGORY = {
    "BeingAtAPlace": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:1259f09e-5379-4629-beb1-0cc94fb413de",
    "Arriving": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:1259f09e-5379-4629-beb1-0cc94fb413de",
    "Leaving": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:1259f09e-5379-4629-beb1-0cc94fb413de",
    "Translocation": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:1259f09e-5379-4629-beb1-0cc94fb413de",
    "Transportation": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:1259f09e-5379-4629-beb1-0cc94fb413de",
    "Voyage": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:1259f09e-5379-4629-beb1-0cc94fb413de",
    "Damaging": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:32205ca1-8866-4c92-ac23-ec5cb1fe05e4",
    "Repairing": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:32205ca1-8866-4c92-ac23-ec5cb1fe05e4",
    "Destroying": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:32205ca1-8866-4c92-ac23-ec5cb1fe05e4",
    "Sinking": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:32205ca1-8866-4c92-ac23-ec5cb1fe05e4",
    "InternalChange": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:32205ca1-8866-4c92-ac23-ec5cb1fe05e4",
    "ScalarChange": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:32205ca1-8866-4c92-ac23-ec5cb1fe05e4",
    "QuantityChange": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:32205ca1-8866-4c92-ac23-ec5cb1fe05e4",
    "Increasing": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:32205ca1-8866-4c92-ac23-ec5cb1fe05e4",
    "Decreasing": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:32205ca1-8866-4c92-ac23-ec5cb1fe05e4",
    "FallingIll": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:32205ca1-8866-4c92-ac23-ec5cb1fe05e4",
    "Healing": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:32205ca1-8866-4c92-ac23-ec5cb1fe05e4",
    "Dying": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:32205ca1-8866-4c92-ac23-ec5cb1fe05e4",
    "BeingDamaged": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:32205ca1-8866-4c92-ac23-ec5cb1fe05e4",
    "BeingDestroyed": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:32205ca1-8866-4c92-ac23-ec5cb1fe05e4",
    "HavingAMedicalCondition": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:32205ca1-8866-4c92-ac23-ec5cb1fe05e4",
    "HavingInternalState+": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:32205ca1-8866-4c92-ac23-ec5cb1fe05e4",
    "HavingInternalState-": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:32205ca1-8866-4c92-ac23-ec5cb1fe05e4",
    "BeingDead": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:32205ca1-8866-4c92-ac23-ec5cb1fe05e4",
    "BeginningARelationship": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:bf031330-bd86-4633-bb40-fe602d63b3c4",
    "AlteringARelationship": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:bf031330-bd86-4633-bb40-fe602d63b3c4",
    "RelationshipChange": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:bf031330-bd86-4633-bb40-fe602d63b3c4",
    "EndingARelationship": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:bf031330-bd86-4633-bb40-fe602d63b3c4",
    "BeginningContractualAgreement": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:bf031330-bd86-4633-bb40-fe602d63b3c4",
    "ExtendingContractualAgreement": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:bf031330-bd86-4633-bb40-fe602d63b3c4",
    "EndingContractualAgreement": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:bf031330-bd86-4633-bb40-fe602d63b3c4",
    "SocialStatusChange": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:bf031330-bd86-4633-bb40-fe602d63b3c4",
    "JoiningAnOrganization": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:bf031330-bd86-4633-bb40-fe602d63b3c4",
    "LeavingAnOrganization": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:bf031330-bd86-4633-bb40-fe602d63b3c4",
    "Replacing": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:bf031330-bd86-4633-bb40-fe602d63b3c4",
    "Mismanagement": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:bf031330-bd86-4633-bb40-fe602d63b3c4",
    "BeingInARelationship": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:bf031330-bd86-4633-bb40-fe602d63b3c4",
    "Collaboration": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:bf031330-bd86-4633-bb40-fe602d63b3c4",
    "HavingContractualAgreement": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:bf031330-bd86-4633-bb40-fe602d63b3c4",
    "BeingAtPeace": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:bf031330-bd86-4633-bb40-fe602d63b3c4",
    "BeingLeader": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:bf031330-bd86-4633-bb40-fe602d63b3c4",
    "BeingEmployed": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:bf031330-bd86-4633-bb40-fe602d63b3c4",
    "TakingUnderControl": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:6e14977b-5eaf-4294-a67a-ac209a4ca095",
    "Enslaving": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:6e14977b-5eaf-4294-a67a-ac209a4ca095",
    "ForceToAct": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:6e14977b-5eaf-4294-a67a-ac209a4ca095",
    "Punishing": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:6e14977b-5eaf-4294-a67a-ac209a4ca095",
    "Occupation": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:6e14977b-5eaf-4294-a67a-ac209a4ca095",
    "StartingConflict": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:9f5c88ad-278c-4e83-9b65-15678a02ac7d",
    "EndingConflict": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:9f5c88ad-278c-4e83-9b65-15678a02ac7d",
    "StartingAWar": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:9f5c88ad-278c-4e83-9b65-15678a02ac7d",
    "ViolentContest": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:9f5c88ad-278c-4e83-9b65-15678a02ac7d",
    "Attacking": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:9f5c88ad-278c-4e83-9b65-15678a02ac7d",
    "Besieging": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:9f5c88ad-278c-4e83-9b65-15678a02ac7d",
    "Invasion": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:9f5c88ad-278c-4e83-9b65-15678a02ac7d",
    "Killing": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:9f5c88ad-278c-4e83-9b65-15678a02ac7d",
    "Uprising": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:9f5c88ad-278c-4e83-9b65-15678a02ac7d",
    "Mutiny": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:9f5c88ad-278c-4e83-9b65-15678a02ac7d",
    "BeingInConflict": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:9f5c88ad-278c-4e83-9b65-15678a02ac7d",
    "Unrest": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:9f5c88ad-278c-4e83-9b65-15678a02ac7d",
    "Communication": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:1814b29d-2c6b-46dc-88a7-5ced1b524f8d",
    "Request": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:1814b29d-2c6b-46dc-88a7-5ced1b524f8d",
    "Encounter": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:1814b29d-2c6b-46dc-88a7-5ced1b524f8d",
    "Visit": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:1814b29d-2c6b-46dc-88a7-5ced1b524f8d",
    "SocialInteraction": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:1814b29d-2c6b-46dc-88a7-5ced1b524f8d",
    "ChangeOfPossession": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:c5ce9be3-1e95-4b90-a71b-f564e38b2f9f",
    "Giving": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:c5ce9be3-1e95-4b90-a71b-f564e38b2f9f",
    "Getting": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:c5ce9be3-1e95-4b90-a71b-f564e38b2f9f",
    "Trade": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:c5ce9be3-1e95-4b90-a71b-f564e38b2f9f",
    "Buying": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:c5ce9be3-1e95-4b90-a71b-f564e38b2f9f",
    "Selling": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:c5ce9be3-1e95-4b90-a71b-f564e38b2f9f",
    "FinancialTransaction": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:c5ce9be3-1e95-4b90-a71b-f564e38b2f9f",
    "LosingPossession": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:c5ce9be3-1e95-4b90-a71b-f564e38b2f9f",
    "Production": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:c5ce9be3-1e95-4b90-a71b-f564e38b2f9f",
    "HavingInPossession": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:c5ce9be3-1e95-4b90-a71b-f564e38b2f9f",
    "BeingInDebt": "https://id.globalise.nl/hdl:20.500.14722/thesaurus:c5ce9be3-1e95-4b90-a71b-f564e38b2f9f"
}

CATEGORY_TO_LABEL = {
    "https://id.globalise.nl/hdl:20.500.14722/thesaurus:bf031330-bd86-4633-bb40-fe602d63b3c4": "Relations, employment, leadership",
    "https://id.globalise.nl/hdl:20.500.14722/thesaurus:32205ca1-8866-4c92-ac23-ec5cb1fe05e4": "Improvement & deterioration",
    "https://id.globalise.nl/hdl:20.500.14722/thesaurus:1259f09e-5379-4629-beb1-0cc94fb413de": "Movement & transport",
    "https://id.globalise.nl/hdl:20.500.14722/thesaurus:c5ce9be3-1e95-4b90-a71b-f564e38b2f9f": "Possession, trade, finances",
    "https://id.globalise.nl/hdl:20.500.14722/thesaurus:1814b29d-2c6b-46dc-88a7-5ced1b524f8d": "Communication & meetings",
    "https://id.globalise.nl/hdl:20.500.14722/thesaurus:9f5c88ad-278c-4e83-9b65-15678a02ac7d": "Conflict & violence",
    "https://id.globalise.nl/hdl:20.500.14722/thesaurus:6e14977b-5eaf-4294-a67a-ac209a4ca095": "Coercion, control, punishment",
}

NER_DATA_DICT = {
    'CMTY_NAME': NerData(
        id='CMTY_NAME',
        uri=f'{ner_base}:cmty_name',
        label='Name of Commodity',
        entity_type=f'{prefix}:Commodity',
        thesaurus_label="Commodity",
        body_type='ClassificatoryStatus',
        classificatory_subject='Dimension'
    ),
    'CMTY_QUAL': NerData(
        id='CMTY_QUAL',
        uri=f'{ner_base}:cmty_qual',
        label='Commodity qualifier: colors, processing',
        entity_type=f'{prefix}:CommodityQualifier',
        thesaurus_label="Qualifier",
        body_type='ClassificatoryStatus',
        classificatory_subject='Dimension'
    ),
    'CMTY_QUANT': NerData(
        id='CMTY_QUANT',
        uri=f'{ner_base}:cmty_quant',
        label='Quantity',
        entity_type=f'{prefix}:CommodityQuantity',
        thesaurus_label="Exchange Unit",
        body_type='Dimension'
    ),
    'DATE': NerData(
        id='DATE',
        uri=f'{ner_base}:date',
        label='Date',
        entity_type=f'{prefix}:Date',
        thesaurus_label="Date",
        body_type='AppellativeStatus',
        appellative_subject='TimeSpan',
        classificatory_subject='Dimension'
    ),
    'DOC': NerData(
        id='DOC',
        uri=f'{ner_base}:doc',
        label='Document',
        entity_type=f'{prefix}:Document',
        thesaurus_label="Document",
        body_type='ClassificatoryStatus',
        classificatory_subject='HumanMadeObject'
    ),
    'ETH_REL': NerData(
        id='ETH_REL',
        uri=f'{ner_base}:eth_rel',
        label='Ethno-religious appellation or attribute, not derived from location name',
        entity_type=f'{prefix}:EthnoReligiousAppellation',
        thesaurus_label="Person",
        body_type='ClassificatoryStatus',
        classificatory_subject='Person'
    ),
    'LOC_ADJ': NerData(
        id='LOC_ADJ',
        uri=f'{ner_base}:loc_adj',
        label='Derived (adjectival) form of location name',
        entity_type=f'{prefix}:Location',
        thesaurus_label="Place",  # But only for the appellative subject here
        body_type='AppellativeStatus',
        appellative_subject='Place'
    ),
    'LOC_NAME': NerData(
        id='LOC_NAME',
        uri=f'{ner_base}:loc_name',
        label='Name of Location',
        entity_type=f'{prefix}:Location',
        thesaurus_label="Place",
        body_type='AppellativeStatus',
        appellative_subject='Place'
    ),
    'ORG': NerData(
        id='ORG',
        uri=f'{ner_base}:org',
        label='Organisation type',
        entity_type=f'{prefix}:OrganisationType',
        thesaurus_label="Organisation",
        body_type='ClassificatoryStatus',
        classificatory_subject='Group'
    ),
    'PER_ATTR': NerData(
        id='PER_ATTR',
        uri=f'{ner_base}:per_attr',
        label='Other persons attributes (than PER or STATUS)',
        entity_type=f'{prefix}:PersonAttribute',
        thesaurus_label="Person",
        body_type='ClassificatoryStatus',
        classificatory_subject='Person'
    ),
    'PER_NAME': NerData(
        id='PER_NAME',
        uri=f'{ner_base}:per_name',
        label='Name of Person',
        entity_type=f'{prefix}:Person',
        thesaurus_label="Person",
        body_type='AppellativeStatus',
        appellative_subject='Person'
    ),
    'PRF': NerData(
        id='PRF',
        uri=f'{ner_base}:prf',
        label='Profession, title',
        entity_type=f'{prefix}:Profession',
        thesaurus_label="Person",
        body_type='ClassificatoryStatus',
        classificatory_subject='Person'
    ),
    'SHIP': NerData(
        id='SHIP',
        uri=f'{ner_base}:ship',
        label='Ship name',
        entity_type=f'{prefix}:Ship',
        thesaurus_label="Ship",
        body_type='AppellativeStatus',
        appellative_subject='HumanMadeObject'
    ),
    'SHIP_TYPE': NerData(
        id='SHIP_TYPE',
        uri=f'{ner_base}:ship_type',
        label='Ship type',
        entity_type=f'{prefix}:Ship',
        thesaurus_label="Ship",
        body_type='ClassificatoryStatus',
        classificatory_subject='HumanMadeObject'
    ),
    'STATUS': NerData(
        id='STATUS',
        uri=f'{ner_base}:status',
        label='(Civic) status',
        entity_type=f'{prefix}:CivicStatus',
        thesaurus_label="Person",
        body_type='ClassificatoryStatus',
        classificatory_subject='Person'
    )
}

event_uri_prefix = "https://w3id.org/globalise/ontology/events/"

EVENT_PREDICATES = {
    "AlteringARelationship": f"{event_uri_prefix}EndingARelationship",
    "Arriving": f"{event_uri_prefix}Arriving",
    "Attacking": f"{event_uri_prefix}Attacking",
    "BeginningARelationship": f"{event_uri_prefix}BeginningARelationship",
    "BeginningContractualAgreement": f"{event_uri_prefix}BeginningContractualAgreement",
    "BeingAtAPlace": f"{event_uri_prefix}BeingAtAPlace",
    "BeingDamaged": f"{event_uri_prefix}BeingDamaged",
    "BeingDead": f"{event_uri_prefix}BeingDead",
    "BeingDestroyed": f"{event_uri_prefix}BeingDestroyed",
    "BeingEmployed": f"{event_uri_prefix}BeingEmployed",
    "BeingInARelationship": f"{event_uri_prefix}BeingInARelationship",
    "BeingInConflict": f"{event_uri_prefix}BeingInConflict",
    "BeingLeader": f"{event_uri_prefix}BeingLeader",
    "Besieging": f"{event_uri_prefix}Besieging",
    "BiologicalEvent": f"{event_uri_prefix}BiologicalEvent",
    "Buying": f"{event_uri_prefix}Buying",
    "ChangeOfPossession": f"{event_uri_prefix}ChangeOfPossession",
    "Collaboration": f"{event_uri_prefix}Collaboration",
    "Damaging": f"{event_uri_prefix}Damaging",
    "Decreasing": f"{event_uri_prefix}Decreasing",
    "Destroying": f"{event_uri_prefix}Destroying",
    "Dying": f"{event_uri_prefix}Dying",
    "EndingARelationship": f"{event_uri_prefix}EndingARelationship",
    "EndingContractualAgreement": f"{event_uri_prefix}EndingContractualAgreement",
    "FallingIll": f"{event_uri_prefix}FallingIll",
    "FinancialTransaction": f"{event_uri_prefix}FinancialTransaction",
    "Getting": f"{event_uri_prefix}Getting",
    "Giving": f"{event_uri_prefix}Giving",
    "HavingAMedicalCondition": f"{event_uri_prefix}HavingAMedicalCondition",
    "HavingInPossession": f"{event_uri_prefix}HavingInPossession",
    "HavingInternalState": f"{event_uri_prefix}HavingInternalState-",
    "HavingInternalState+": f"{event_uri_prefix}HavingInternalState+",
    "Healing": f"{event_uri_prefix}Healing",
    "Increasing": f"{event_uri_prefix}Increasing",
    "IntentionalDamaging": f"{event_uri_prefix}IntentionalDamaging",
    "IntentionalEvent": f"{event_uri_prefix}IntentionalEvent",
    "InternalChange": f"{event_uri_prefix}InternalChange",
    "Invasion": f"{event_uri_prefix}Invasion",
    "JoiningAnOrganization": f"{event_uri_prefix}JoiningAnOrganization",
    "Leaving": f"{event_uri_prefix}Leaving",
    "LeavingAnOrganization": f"{event_uri_prefix}LeavingAnOrganization",
    "Miscellaneous": f"{event_uri_prefix}Miscellaneous",
    "Mutiny": f"{event_uri_prefix}Mutiny",
    "Occupation": f"{event_uri_prefix}Occupation",
    "PoliticalRevolution": f"{event_uri_prefix}PoliticalRevolution",
    "QuantityChange": f"{event_uri_prefix}QuantityChange",
    "RelationshipChange": f"{event_uri_prefix}RelationshipChange",
    "Repairing": f"{event_uri_prefix}Repairing",
    "Replacing": f"{event_uri_prefix}Replacing",
    "Riot": f"{event_uri_prefix}Riot",
    "ScalarChange": f"{event_uri_prefix}ScalarChange",
    "Selling": f"{event_uri_prefix}Selling",
    "Shooting": f"{event_uri_prefix}Shooting",
    "SocialInteraction": f"{event_uri_prefix}SocialInteraction",
    "SocialStatusChange": f"{event_uri_prefix}SocialStatusChange",
    "TakingSomeoneUnderControl": f"{event_uri_prefix}TakingSomeoneUnderControl",
    "TransLocation": f"{event_uri_prefix}TransLocation",
    "Transportation": f"{event_uri_prefix}Transportation",
    "Uprising": f"{event_uri_prefix}Uprising",
    "ViolentContest": f"{event_uri_prefix}ViolentContest",
    "ViolentTranslocation": f"{event_uri_prefix}ViolentTranslocation",
    "Voyage": f"{event_uri_prefix}Voyage",
    "War": f"{event_uri_prefix}War"
}

EVENT_ARGUMENTS = [
    "Agent",
    "AgentPatient",
    "Miscellaneous",
    "Benefactive",
    "Cargo",
    "Instrument",
    "Location",
    "Patient",
    "Source",
    "Target",
    "Time"
]
