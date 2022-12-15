#!/usr/bin/env python3
import glob
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict

from icecream import ic

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


@dataclass
class WebAnnoLine:
    pass


@dataclass
class WAHeadLine(WebAnnoLine):
    contents: str


@dataclass
class WABodyLine(WebAnnoLine):
    sentence_num: int
    token_num: float
    begin_offset: int
    end_offset: int
    token: str
    col3: str
    col4: str
    col5: str
    col6: str
    col7: str
    col8: str
    col9: str


def wa_decode(string: str) -> str:
    return string.replace("\\_", '_') \
        .replace('\\[', '[') \
        .replace('\\]', ']') \
        .replace('\\|', '|') \
        .replace('\\->', '->') \
        .replace('\\;', ';') \
        .replace('\\\t', '\t') \
        .replace('\\n', '\n') \
        .replace('\\*', '*') \
        .replace('\\\\', '\\')


def web_anno_file_paths(dir: str) -> List[str]:
    return glob.glob(f"{dir}/*.tsv")


def as_web_annotation(line: WABodyLine) -> Dict[str, any]:
    class_name = line.col4.split("[")[0]
    body = {
        "@context": {"tt": "https://brambg.github.io/ns/team-text#"},
        "type": "tt:Entity",
        "class_name": class_name,
        "class_description": entities[class_name],
        "url": line.col3.split("[")[0]
    }
    target = []
    anno_uuid = uuid.uuid4()
    return {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "id": f"urn:globalise:annotation:{anno_uuid}",
        "type": "Annotation",
        "motivation": "tagging",
        "generated": datetime.today().isoformat(),  # use last-modified from pagexml for px: types
        "body": body,
        "target": target
    }


def extract_annotations(path: str) -> List[Dict[str, any]]:
    lines = []
    with open(path) as tsv:
        for l in tsv.readlines():
            line = l.strip()
            if line.startswith("#"):
                wal = WAHeadLine(contents=line.removeprefix('#'))
                lines.append(wal)
            elif line:
                parts = wa_decode(line).split('\t')
                (sentence_num, token_num) = parts[0].split('-')
                (begin_offset, end_offset) = parts[1].split('-')
                wal = WABodyLine(
                    sentence_num=int(sentence_num),
                    token_num=float(token_num),
                    begin_offset=int(begin_offset),
                    end_offset=int(end_offset),
                    token=parts[2],
                    col3=parts[3],
                    col4=parts[4],
                    col5=parts[5],
                    col6=parts[6],
                    col7=parts[7],
                    col8=parts[8],
                    col9=parts[9]
                )
                lines.append(wal)
            else:
                ic(line)

    ic(lines)
    interesting_lines = [l for l in lines if type(l) is WABodyLine and "http" in l.col3]
    ic(interesting_lines)
    web_annotations = [as_web_annotation(l) for l in interesting_lines]
    return web_annotations


def main():
    annotations = []
    for p in web_anno_file_paths(data_dir):
        annotations.append(extract_annotations(p))
    ic(annotations)


if __name__ == '__main__':
    main()
