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

ner_base = 'https://digitaalerfgoed.poolparty.biz/globalise/annotation/ner'
prefix = 'urn:globalise:entityType'
NER_DATA_DICT = {
    'CMTY_NAME': {
        'uri': f'{ner_base}/CMTY_NAME',
        'label': 'Name of Commodity',
        'entity_type': f'{prefix}:Commodity'
    },
    'CMTY_QUAL': {
        'uri': f'{ner_base}/CMTY_QUAL',
        'label': 'Commodity qualifier: colors, processing',
        'entity_type': f'{prefix}:CommodityQualifier'
    },
    'CMTY_QUANT': {
        'uri': f'{ner_base}/CMTY_QUANT',
        'label': 'Quantity',
        'entity_type': f'{prefix}:CommodityQuantity'
    },
    'DATE': {
        'uri': f'{ner_base}/DATE',
        'label': 'Date',
        'entity_type': f'{prefix}:Date'
    },
    'DOC': {
        'uri': f'{ner_base}/DOC',
        'label': 'Document',
        'entity_type': f'{prefix}:Document'
    },
    'ETH_REL': {
        'uri': f'{ner_base}/ETH_REL',
        'label': 'Ethno-religious appellation or attribute, not derived from location name',
        'entity_type': f'{prefix}:EthnoReligiousAppellation'
    },
    'LOC_ADJ': {
        'uri': f'{ner_base}/LOC_ADJ',
        'label': 'Derived (adjectival) form of location name',
        'entity_type': f'{prefix}:Location'
    },
    'LOC_NAME': {
        'uri': f'{ner_base}/LOC_NAME',
        'label': 'Name of Location',
        'entity_type': f'{prefix}:Location'
    },
    'ORG': {
        'uri': f'{ner_base}/ORG',
        'label': 'Organisation name',
        'entity_type': f'{prefix}:Organisation'
    },
    'PER_ATTR': {
        'uri': f'{ner_base}/PER_ATTR',
        'label': 'Other persons attributes (than PER or STATUS)',
        'entity_type': f'{prefix}:PersonAttribute'
    },
    'PER_NAME': {
        'uri': f'{ner_base}/PER_NAME',
        'label': 'Name of Person',
        'entity_type': f'{prefix}:Person'
    },
    'PRF': {
        'uri': f'{ner_base}/PRF',
        'label': 'Profession, title',
        'entity_type': f'{prefix}:Profession'
    },
    'SHIP': {
        'uri': f'{ner_base}/SHIP',
        'label': 'Ship name',
        'entity_type': f'{prefix}:Ship'
    },
    'SHIP_TYPE': {
        'uri': f'{ner_base}/SHIP_TYPE',
        'label': 'Ship type',
        'entity_type': f'{prefix}:Ship'
    },
    'STATUS': {
        'uri': f'{ner_base}/STATUS',
        'label': '(Civic) status',
        'entity_type': f'{prefix}:CivicStatus'
    }
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
