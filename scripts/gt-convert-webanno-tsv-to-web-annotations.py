#!/usr/bin/env python3
import glob
import json
import uuid
from datetime import datetime
from typing import List, Dict

from icecream import ic
from loguru import logger

from globalise_tools.webanno_tsv_tools import process_webanno_tsv_file2

data_dir = "data/inception_output"

entities = {"CIV": "Civic/legal mention",
            "CMTY": "Commodity",
            "CMTY_QUAL": "Commodity qualifier, if appears to be relevant for subclassification of commodity",
            "DOC": "Document",
            "DYN": "Dynasty",
            "ERL": "Ethno-religious/location-based individual",
            "ERL_QUAL": "Ethno-religious/location-based qualifier",
            "LOC": "Location",
            "MES": "Measure",
            "MES_CUR": "Currency (measure)",
            "NUM": "Numerical (exact) quantity",
            "ORG": "Named organisation",
            "PER": "Person",
            "POL": "Politie",
            "POL_LOC": "Politie+location",
            "PRF": "Profession",
            "RNK": "Rank / title",
            "SHIP": "Ship name",
            "SHIP_TYPE": "ship type:",
            "TIME_DATE": "Date (specific point in time)",
            "TIME_DUR": "Duration",
            "TIME_REL": "Time relation marker",
            "UNFREE": "Slaves en related terms"}

event_predicates = {
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

event_arguments = ["Agent",
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


@logger.catch
def main():
    annotations = []
    for p in web_anno_file_paths(data_dir):
        ic(p)
        annotations.extend(extract_annotations(p))
    print(json.dumps(annotations, indent=2))


def web_anno_file_paths(directory: str) -> List[str]:
    return glob.glob(f"{directory}/*.tsv")


def extract_annotations(path: str) -> List[Dict[str, any]]:
    doc_id = path.split('/')[-1].replace('.tsv', '')

    word_annotations, token_annotations = load_word_and_token_annotations(doc_id)
    word_web_annotations = load_word_web_annotations(doc_id)

    tokens, wat_annotations = process_webanno_tsv_file2(path)
    entity_webanno = [a for a in wat_annotations if
                      a.layers[0].label == "de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity"]
    ic(entity_webanno)
    # ic(w3c_annotations)

    # web_annotations = from_wat_lines(doc_id, path, token_annotations, word_annotations, word_web_annotations)
    web_annotations = from_webanno(entity_webanno, token_annotations, word_annotations, word_web_annotations)
    return web_annotations


def load_word_and_token_annotations(doc_id):
    with open(f"out/{doc_id}-metadata.json") as jf:
        metadata = json.load(jf)
    # ic(metadata)
    word_annotations = [a for a in metadata["annotations"] if a["type"] == "tt:Word"]
    token_annotations = [a for a in metadata["annotations"] if a["type"] == "tt:Token"]
    # ic(word_annotations)
    return word_annotations, token_annotations


def load_word_web_annotations(doc_id):
    with open(f"out/{doc_id}-web-annotations.json") as jf:
        all_annotations = json.load(jf)
    word_web_annotations = [a for a in all_annotations if a["body"]["type"] == "tt:Word"]
    return word_web_annotations


def from_webanno(entity_webanno, token_annotations, word_annotations, word_web_annotations):
    w3c_annotations = []
    for ea in entity_webanno:
        if len(ea.layers) != 1 or len(ea.layers[0].elements) != 1:
            ic(ea)
            continue
            # raise Exception(f"!unexpected number of layers/elements in {ea}")

        body = make_body(ea)
        targets = make_targets(ea, token_annotations, word_annotations, word_web_annotations)

        anno_uuid = uuid.uuid4()
        w3c_anno = {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "id": f"urn:globalise:annotation:{anno_uuid}",
            "type": "Annotation",
            "motivation": "tagging",
            "generated": datetime.today().isoformat(),  # TODO: use last-modified from pagexml for px: types
            "body": body,
            "target": targets
        }
        w3c_annotations.append(w3c_anno)
    return w3c_annotations


def make_body(ea):
    fields = ea.layers[0].elements[0].fields
    if "value" not in fields:
        ic(ea)
        return {}
    class_name = fields["value"]
    e_uuid = uuid.uuid4()
    body = {
        "@context": {"tt": "https://brambg.github.io/ns/team-text#"},
        "type": "tt:Entity",
        "id": f"urn:globalise:entity:{e_uuid}",
        "class_name": class_name,
        "class_description": entities[class_name],
        "text": ea.text
    }
    if "identifier" in fields:
        body["url"] = fields["identifier"]
    return body


def make_targets(ea, token_annotations, word_annotations, word_web_annotations):
    targets = []
    for i in ea.token_idxs:
        token_annotation = token_annotations[i]
        token_range_begin = token_annotation["offset"]
        token_range_end = token_range_begin + token_annotation["length"]
        relevant_word_annotations = [a for a in word_annotations if
                                     word_annotation_covers_token_range(a, token_range_begin, token_range_end)]
        for wa in relevant_word_annotations:
            for wwa in [a for a in word_web_annotations if a["body"]["id"] == wa["id"]]:
                targets.extend(wwa["target"])
    return targets


def word_annotation_covers_token_range(annotation, token_range_begin, token_range_end):
    annotation_range_begin = annotation["offset"]
    annotation_range_end = annotation_range_begin + annotation["length"]
    return token_range_begin >= annotation_range_begin and token_range_end <= annotation_range_end


if __name__ == '__main__':
    main()
