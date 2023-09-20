#!/usr/bin/env python3
import json
import pathlib
import uuid

import cassis
import hydra
from loguru import logger
from omegaconf import DictConfig

ENTITIES = {"CIV": "Civic/legal mention",
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
            "UNFREE": "Slaves en related terms"}

EVENT_PREDICATES = {
    "AlteringARelationship": "https://github.com/globalise-huygens/nlp-event-detection/wiki#EndingARelationship",
    "Arriving": "https://github.com/globalise-huygens/nlp-event-detection/wiki#Arriving",
    "Attacking": "https://github.com/globalise-huygens/nlp-event-detection/wiki#Attacking",
    "BeginningARelationship": "https://github.com/globalise-huygens/nlp-event-detection/wiki#BeginningARelationship",
    "BeginningContractualAgreement": "https://github.com/globalise-huygens/nlp-event-detection/wiki#BeginningContractualAgreement",
    "BeingAtAPlace": "https://github.com/globalise-huygens/nlp-event-detection/wiki#BeingAtAPlace",
    "BeingDamaged": "https://github.com/globalise-huygens/nlp-event-detection/wiki#BeingDamaged",
    "BeingDead": "https://github.com/globalise-huygens/nlp-event-detection/wiki#BeingDead",
    "BeingDestroyed": "https://github.com/globalise-huygens/nlp-event-detection/wiki#BeingDestroyed",
    "BeingEmployed": "https://github.com/globalise-huygens/nlp-event-detection/wiki#BeingEmployed",
    "BeingInARelationship": "https://github.com/globalise-huygens/nlp-event-detection/wiki#BeingInARelationship",
    "BeingInConflict": "https://github.com/globalise-huygens/nlp-event-detection/wiki#BeingInConflict",
    "BeingLeader": "https://github.com/globalise-huygens/nlp-event-detection/wiki#BeingLeader",
    "Besieging": "https://github.com/globalise-huygens/nlp-event-detection/wiki#Besieging",
    "BiologicalEvent": "https://github.com/globalise-huygens/nlp-event-detection/wiki#BiologicalEvent",
    "Buying": "https://github.com/globalise-huygens/nlp-event-detection/wiki#Buying",
    "ChangeOfPossession": "https://github.com/globalise-huygens/nlp-event-detection/wiki#ChangeOfPossession",
    "Collaboration": "https://github.com/globalise-huygens/nlp-event-detection/wiki#Collaboration",
    "Damaging": "https://github.com/globalise-huygens/nlp-event-detection/wiki#Damaging",
    "Decreasing": "https://github.com/globalise-huygens/nlp-event-detection/wiki#Decreasing",
    "Destroying": "https://github.com/globalise-huygens/nlp-event-detection/wiki#Destroying",
    "Dying": "https://github.com/globalise-huygens/nlp-event-detection/wiki#Dying",
    "EndingARelationship": "https://github.com/globalise-huygens/nlp-event-detection/wiki#EndingARelationship",
    "EndingContractualAgreement": "https://github.com/globalise-huygens/nlp-event-detection/wiki#EndingContractualAgreement",
    "FallingIll": "https://github.com/globalise-huygens/nlp-event-detection/wiki#FallingIll",
    "FinancialTransaction": "https://github.com/globalise-huygens/nlp-event-detection/wiki#FinancialTransaction",
    "Getting": "https://github.com/globalise-huygens/nlp-event-detection/wiki#Getting",
    "Giving": "https://github.com/globalise-huygens/nlp-event-detection/wiki#Giving",
    "HavingAMedicalCondition": "https://github.com/globalise-huygens/nlp-event-detection/wiki#HavingAMedicalCondition",
    "HavingInPossession": "https://github.com/globalise-huygens/nlp-event-detection/wiki#HavingInPossession",
    "HavingInternalState": "https://github.com/globalise-huygens/nlp-event-detection/wiki#HavingInternalState-",
    "HavingInternalState+": "https://github.com/globalise-huygens/nlp-event-detection/wiki#HavingInternalState+",
    "Healing": "https://github.com/globalise-huygens/nlp-event-detection/wiki#Healing",
    "Increasing": "https://github.com/globalise-huygens/nlp-event-detection/wiki#Increasing",
    "IntentionalDamaging": "https://github.com/globalise-huygens/nlp-event-detection/wiki#IntentionalDamaging",
    "IntentionalEvent": "https://github.com/globalise-huygens/nlp-event-detection/wiki#IntentionalEvent",
    "InternalChange": "https://github.com/globalise-huygens/nlp-event-detection/wiki#InternalChange",
    "Invasion": "https://github.com/globalise-huygens/nlp-event-detection/wiki#Invasion",
    "JoiningAnOrganization": "https://github.com/globalise-huygens/nlp-event-detection/wiki#JoiningAnOrganization",
    "Leaving": "https://github.com/globalise-huygens/nlp-event-detection/wiki#Leaving",
    "LeavingAnOrganization": "https://github.com/globalise-huygens/nlp-event-detection/wiki#LeavingAnOrganization",
    "Miscellaneous": "https://github.com/globalise-huygens/nlp-event-detection/wiki#Miscellaneous",
    "Mutiny": "https://github.com/globalise-huygens/nlp-event-detection/wiki#Mutiny",
    "Occupation": "https://github.com/globalise-huygens/nlp-event-detection/wiki#Occupation",
    "PoliticalRevolution": "https://github.com/globalise-huygens/nlp-event-detection/wiki#PoliticalRevolution",
    "QuantityChange": "https://github.com/globalise-huygens/nlp-event-detection/wiki#QuantityChange",
    "RelationshipChange": "https://github.com/globalise-huygens/nlp-event-detection/wiki#RelationshipChange",
    "Repairing": "https://github.com/globalise-huygens/nlp-event-detection/wiki#Repairing",
    "Replacing": "https://github.com/globalise-huygens/nlp-event-detection/wiki#Replacing",
    "Riot": "https://github.com/globalise-huygens/nlp-event-detection/wiki#Riot",
    "ScalarChange": "https://github.com/globalise-huygens/nlp-event-detection/wiki#ScalarChange",
    "Selling": "https://github.com/globalise-huygens/nlp-event-detection/wiki#Selling",
    "Shooting": "https://github.com/globalise-huygens/nlp-event-detection/wiki#Shooting",
    "SocialInteraction": "https://github.com/globalise-huygens/nlp-event-detection/wiki#SocialInteraction",
    "SocialStatusChange": "https://github.com/globalise-huygens/nlp-event-detection/wiki#SocialStatusChange",
    "TakingSomeoneUnderControl": "https://github.com/globalise-huygens/nlp-event-detection/wiki#TakingSomeoneUnderControl",
    "TransLocation": "https://github.com/globalise-huygens/nlp-event-detection/wiki#TransLocation",
    "Transportation": "https://github.com/globalise-huygens/nlp-event-detection/wiki#Transportation",
    "Uprising": "https://github.com/globalise-huygens/nlp-event-detection/wiki#Uprising",
    "ViolentContest": "https://github.com/globalise-huygens/nlp-event-detection/wiki#ViolentContest",
    "ViolentTranslocation": "https://github.com/globalise-huygens/nlp-event-detection/wiki#ViolentTranslocation",
    "Voyage": "https://github.com/globalise-huygens/nlp-event-detection/wiki#Voyage",
    "War": "https://github.com/globalise-huygens/nlp-event-detection/wiki#War"}

EVENT_ARGUMENTS = ["Agent",
                   "AgentPatient",
                   "Miscellaneous",
                   "Benefactive",
                   "Cargo",
                   "Instrument",
                   "Location",
                   "Patient",
                   "Source",
                   "Target",
                   "Time"]

NAMED_ENTITY_LAYER_NAME = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity"
EVENT_LAYER_NAME = "webanno.custom.SemPredGLOB"


@hydra.main(version_base=None)
@logger.catch
def main(cfg: DictConfig) -> None:
    base = '/Users/bram/workspaces/globalise'
    with open(f'{base}/globalise-tools/data/typesystem.xml', 'rb') as f:
        typesystem = cassis.load_typesystem(f)

    inception_export_path = pathlib.Path(f"{base}/globalise-tools/data/inception_output/")
    xmi_paths = list(inception_export_path.glob("*.xmi"))

    for path in sorted(xmi_paths):
        logger.info(f'<= {path}')
        with open(path, 'rb') as f:
            cas = cassis.load_cas_from_xmi(f, typesystem=typesystem)
        logger.info(f"{len(cas.views)} views")
        main_view = cas.views[0]
        named_entity_annotations = [a for a in main_view.get_all_annotations() if
                                    a.type.name == NAMED_ENTITY_LAYER_NAME]
        glob_annotations = [a for a in main_view.get_all_annotations() if
                            a.type.name == EVENT_LAYER_NAME]
        semarg_annotations = [a for a in main_view.get_all_annotations() if
                              a.type.name == "de.tudarmstadt.ukp.dkpro.core.api.semantics.type.SemArg"]
        print(f"{len(named_entity_annotations)} ne annotations")
        if named_entity_annotations:
            print(named_entity_annotations[0])

        for nea in named_entity_annotations:
            e_uuid = uuid.uuid4()
            class_name = nea.value
            if not class_name:
                logger.warning(f"no className for {nea}")
            else:
                if class_name not in ENTITIES:
                    logger.error(f"unknown className: {class_name} in {nea}")
                else:
                    body = {
                        "@context": {"@vocab": "https://knaw-huc.github.io/ns/team-text#"},
                        "type": "Entity",
                        "id": f"urn:globalise:entity:{e_uuid}",
                        "metadata": {
                            "type": "EntityMetadata",
                            "className": class_name,
                            "classDescription": ENTITIES[class_name],
                            "beginChar": nea.begin,
                            "endChar": nea.end,
                            "text": nea.get_covered_text(),
                        }
                    }
                    print(json.dumps(body, indent=4))
        print()

        print(f"{len(glob_annotations)} glob annotations")
        if glob_annotations:
            print(glob_annotations[0])
        for ga in glob_annotations:
            print(
                f'begin_char={ga.begin}, end_char={ga.end}, text="{ga.get_covered_text()}", category={ga.category}, relationtype={ga.relationtype}')

        print()

        print(f"{len(semarg_annotations)} semarg annotations")
        for sa in semarg_annotations:
            print(f'begin_char={sa.begin}, end_char={sa.end}, text="{sa.get_covered_text()}"')
        print()


if __name__ == '__main__':
    main()


"""
TODO:
- map inception entity annotations to text and image targets
- when creating the xmi, store the text range for the words
- per word, store the image coords and the textanchor range
- now
"""