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

ner_base = "https://data.globalise.huygens.knaw.nl/hdl:20.500.14722/thesaurus"
prefix = 'urn:example:globalise:entityType'


@dataclass
class NerData:
    id: str
    uri: str
    label: str
    entity_type: str
    body_type: str
    classificatory_subject: Optional[str] = None
    appellative_subject: Optional[str] = None


NER_DATA_DICT = {
    'CMTY_NAME': NerData(
        id='CMTY_NAME',
        uri=f'{ner_base}:cmty_name',
        label='Name of Commodity',
        entity_type=f'{prefix}:Commodity',
        body_type='ClassificatoryStatus',
        classificatory_subject='Dimension'
    ),
    'CMTY_QUAL': NerData(
        id='CMTY_QUAL',
        uri=f'{ner_base}:cmty_qual',
        label='Commodity qualifier: colors, processing',
        entity_type=f'{prefix}:CommodityQualifier',
        body_type='ClassificatoryStatus',
        classificatory_subject='PhysicalThing'
    ),
    'CMTY_QUANT': NerData(
        id='CMTY_QUANT',
        uri=f'{ner_base}:cmty_quant',
        label='Quantity',
        entity_type=f'{prefix}:CommodityQuantity',
        body_type='Dimension'
    ),
    'DATE': NerData(
        id='DATE',
        uri=f'{ner_base}:date',
        label='Date',
        entity_type=f'{prefix}:Date',
        body_type='AppellativeStatus',
        appellative_subject='TimeSpan',
        classificatory_subject='Dimension'
    ),
    'DOC': NerData(
        id='DOC',
        uri=f'{ner_base}:doc',
        label='Document',
        entity_type=f'{prefix}:Document',
        body_type='ClassificatoryStatus',
        classificatory_subject='HumanMadeObject'
    ),
    'ETH_REL': NerData(
        id='ETH_REL',
        uri=f'{ner_base}:eth_rel',
        label='Ethno-religious appellation or attribute, not derived from location name',
        entity_type=f'{prefix}:EthnoReligiousAppellation',
        body_type='ClassificatoryStatus',
        classificatory_subject='Person'
    ),
    'LOC_ADJ': NerData(
        id='LOC_ADJ',
        uri=f'{ner_base}:loc_adj',
        label='Derived (adjectival) form of location name',
        entity_type=f'{prefix}:Location',
        body_type='AppellativeStatus',
        appellative_subject='Place'
    ),
    'LOC_NAME': NerData(
        id='LOC_NAME',
        uri=f'{ner_base}:loc_name',
        label='Name of Location',
        entity_type=f'{prefix}:Location',
        body_type='AppellativeStatus',
        appellative_subject='Place'
    ),
    'ORG': NerData(
        id='ORG',
        uri=f'{ner_base}:org',
        label='Organisation type',
        entity_type=f'{prefix}:OrganisationType',
        body_type='ClassificatoryStatus',
        classificatory_subject='Group'
    ),
    'PER_ATTR': NerData(
        id='PER_ATTR',
        uri=f'{ner_base}:per_attr',
        label='Other persons attributes (than PER or STATUS)',
        entity_type=f'{prefix}:PersonAttribute',
        body_type='ClassificatoryStatus',
        classificatory_subject='Person'
    ),
    'PER_NAME': NerData(
        id='PER_NAME',
        uri=f'{ner_base}:per_name',
        label='Name of Person',
        entity_type=f'{prefix}:Person',
        body_type='AppellativeStatus',
        appellative_subject='Person'
    ),
    'PRF': NerData(
        id='PRF',
        uri=f'{ner_base}:prf',
        label='Profession, title',
        entity_type=f'{prefix}:Profession',
        body_type='ClassificatoryStatus',
        classificatory_subject='Person'
    ),
    'SHIP': NerData(
        id='SHIP',
        uri=f'{ner_base}:ship',
        label='Ship name',
        entity_type=f'{prefix}:Ship',
        body_type='AppellativeStatus',
        appellative_subject='HumanMadeObject'
    ),
    'SHIP_TYPE': NerData(
        id='SHIP_TYPE',
        uri=f'{ner_base}:ship_type',
        label='Ship type',
        entity_type=f'{prefix}:Ship',
        body_type='ClassificatoryStatus',
        classificatory_subject='HumanMadeObject'
    ),
    'STATUS': NerData(
        id='STATUS',
        uri=f'{ner_base}:status',
        label='(Civic) status',
        entity_type=f'{prefix}:CivicStatus',
        body_type='ClassificatoryStatus',
        classificatory_subject='Person'
    )
}

wiki_base = "https://github.com/globalise-huygens/nlp-event-detection/wiki#"

EVENT_PREDICATES = {
    "AlteringARelationship": f"{wiki_base}EndingARelationship",
    "Arriving": f"{wiki_base}Arriving",
    "Attacking": f"{wiki_base}Attacking",
    "BeginningARelationship": f"{wiki_base}BeginningARelationship",
    "BeginningContractualAgreement": f"{wiki_base}BeginningContractualAgreement",
    "BeingAtAPlace": f"{wiki_base}BeingAtAPlace",
    "BeingDamaged": f"{wiki_base}BeingDamaged",
    "BeingDead": f"{wiki_base}BeingDead",
    "BeingDestroyed": f"{wiki_base}BeingDestroyed",
    "BeingEmployed": f"{wiki_base}BeingEmployed",
    "BeingInARelationship": f"{wiki_base}BeingInARelationship",
    "BeingInConflict": f"{wiki_base}BeingInConflict",
    "BeingLeader": f"{wiki_base}BeingLeader",
    "Besieging": f"{wiki_base}Besieging",
    "BiologicalEvent": f"{wiki_base}BiologicalEvent",
    "Buying": f"{wiki_base}Buying",
    "ChangeOfPossession": f"{wiki_base}ChangeOfPossession",
    "Collaboration": f"{wiki_base}Collaboration",
    "Damaging": f"{wiki_base}Damaging",
    "Decreasing": f"{wiki_base}Decreasing",
    "Destroying": f"{wiki_base}Destroying",
    "Dying": f"{wiki_base}Dying",
    "EndingARelationship": f"{wiki_base}EndingARelationship",
    "EndingContractualAgreement": f"{wiki_base}EndingContractualAgreement",
    "FallingIll": f"{wiki_base}FallingIll",
    "FinancialTransaction": f"{wiki_base}FinancialTransaction",
    "Getting": f"{wiki_base}Getting",
    "Giving": f"{wiki_base}Giving",
    "HavingAMedicalCondition": f"{wiki_base}HavingAMedicalCondition",
    "HavingInPossession": f"{wiki_base}HavingInPossession",
    "HavingInternalState": f"{wiki_base}HavingInternalState-",
    "HavingInternalState+": f"{wiki_base}HavingInternalState+",
    "Healing": f"{wiki_base}Healing",
    "Increasing": f"{wiki_base}Increasing",
    "IntentionalDamaging": f"{wiki_base}IntentionalDamaging",
    "IntentionalEvent": f"{wiki_base}IntentionalEvent",
    "InternalChange": f"{wiki_base}InternalChange",
    "Invasion": f"{wiki_base}Invasion",
    "JoiningAnOrganization": f"{wiki_base}JoiningAnOrganization",
    "Leaving": f"{wiki_base}Leaving",
    "LeavingAnOrganization": f"{wiki_base}LeavingAnOrganization",
    "Miscellaneous": f"{wiki_base}Miscellaneous",
    "Mutiny": f"{wiki_base}Mutiny",
    "Occupation": f"{wiki_base}Occupation",
    "PoliticalRevolution": f"{wiki_base}PoliticalRevolution",
    "QuantityChange": f"{wiki_base}QuantityChange",
    "RelationshipChange": f"{wiki_base}RelationshipChange",
    "Repairing": f"{wiki_base}Repairing",
    "Replacing": f"{wiki_base}Replacing",
    "Riot": f"{wiki_base}Riot",
    "ScalarChange": f"{wiki_base}ScalarChange",
    "Selling": f"{wiki_base}Selling",
    "Shooting": f"{wiki_base}Shooting",
    "SocialInteraction": f"{wiki_base}SocialInteraction",
    "SocialStatusChange": f"{wiki_base}SocialStatusChange",
    "TakingSomeoneUnderControl": f"{wiki_base}TakingSomeoneUnderControl",
    "TransLocation": f"{wiki_base}TransLocation",
    "Transportation": f"{wiki_base}Transportation",
    "Uprising": f"{wiki_base}Uprising",
    "ViolentContest": f"{wiki_base}ViolentContest",
    "ViolentTranslocation": f"{wiki_base}ViolentTranslocation",
    "Voyage": f"{wiki_base}Voyage",
    "War": f"{wiki_base}War"
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
