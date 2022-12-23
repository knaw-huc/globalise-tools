#!/usr/bin/env python3
import glob
import json
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
    doc_id: str
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


def as_web_annotation(line: WABodyLine, targets) -> Dict[str, any]:
    class_name = line.col4.split("[")[0]
    body = {
        "@context": {"tt": "https://brambg.github.io/ns/team-text#"},
        "type": "tt:Entity",
        "class_name": class_name,
        "class_description": entities[class_name],
        "url": line.col3.split("[")[0],
        "text": line.token
    }

    anno_uuid = uuid.uuid4()
    return {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "id": f"urn:globalise:annotation:{anno_uuid}",
        "type": "Annotation",
        "motivation": "tagging",
        "generated": datetime.today().isoformat(),  # use last-modified from pagexml for px: types
        "body": body,
        "target": targets
    }


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


def extract_annotations(path: str) -> List[Dict[str, any]]:
    doc_id = path.split('/')[-1].replace('.tsv', '')

    word_annotations, token_annotations = load_word_and_token_annotations(doc_id)
    word_web_annotations = load_word_web_annotations(doc_id)

    lines, sentence_token_index = process_webanno_tsv_file(path, doc_id)
    # wat_annotations = process_webanno_tsv_file2(path)
    # ic(wat_annotations)

    # ic(lines)
    interesting_lines = [l for l in lines if type(l) is WABodyLine and "http" in l.col3]
    # ic(interesting_lines)

    web_annotations = []
    for il in interesting_lines:
        key = f"{il.sentence_num}-{int(il.token_num)}"
        abs_token_num = sentence_token_index[key]
        token_annotation = token_annotations[abs_token_num]
        token_range_begin = token_annotation["offset"]
        token_range_end = token_range_begin + token_annotation["length"]
        relevant_word_annotations = [a for a in word_annotations if
                                     word_annotation_covers_token_range(a, token_range_begin, token_range_end)]
        # if not relevant_word_annotations:
        #     ic(token_range_begin, token_range_end, il.token)
        targets = []
        for wa in relevant_word_annotations:
            for wwa in [a for a in word_web_annotations if a["body"]["id"] == wa["id"]]:
                targets.extend(wwa["target"])
        web_annotations.append(as_web_annotation(il, targets))

        # ic(il, token_annotation, relevant_word_annotations)
    return web_annotations


def process_webanno_tsv_file(path: str, doc_id: str):
    lines = []
    sentence_token_index = {}
    token_count = 0
    with open(path) as tsv:
        for line_num, l in enumerate(tsv.readlines()):
            line = l.strip()
            if line.startswith("#"):
                wal = WAHeadLine(contents=line.removeprefix('#'))
                lines.append(wal)
            elif line:
                parts = wa_decode(line).split('\t')
                sen_tok_num = parts[0]
                (sentence_num, token_num) = sen_tok_num.split('-')
                (begin_offset, end_offset) = parts[1].split('-')
                wal = WABodyLine(
                    doc_id=doc_id,
                    sentence_num=int(sentence_num),
                    token_num=float(token_num),
                    begin_offset=int(begin_offset),
                    end_offset=int(end_offset),
                    token=nth_element(parts, 2),
                    col3=nth_element(parts, 3),
                    col4=nth_element(parts, 4),
                    col5=nth_element(parts, 5),
                    col6=nth_element(parts, 6),
                    col7=nth_element(parts, 7),
                    col8=nth_element(parts, 8),
                    col9=nth_element(parts, 9)
                )
                lines.append(wal)
                key = f"{wal.sentence_num}-{int(wal.token_num)}"
                if key not in sentence_token_index:
                    sentence_token_index[key] = token_count
                    token_count += 1
            else:
                # ic(line)
                pass
    return lines, sentence_token_index


def word_annotation_covers_token_range(annotation, token_range_begin, token_range_end):
    annotation_range_begin = annotation["offset"]
    annotation_range_end = annotation_range_begin + annotation["length"]
    return token_range_begin >= annotation_range_begin and token_range_end <= annotation_range_end


def nth_element(parts, n):
    return parts[n] if n < len(parts) else "_"


def main():
    annotations = []
    for p in web_anno_file_paths(data_dir):
        ic(p)
        annotations.append(extract_annotations(p))
    print(json.dumps(annotations, indent=2))


if __name__ == '__main__':
    main()
