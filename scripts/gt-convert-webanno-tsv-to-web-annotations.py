#!/usr/bin/env python3
import glob
import json
import uuid
from dataclasses import dataclass
from datetime import datetime

from loguru import logger
from pagexml.model.physical_document_model import Coords

import globalise_tools.tools as gt
from globalise_tools.events import EVENT_LAYER_NAME, NAMED_ENTITY_LAYER_NAME, ENTITIES
from globalise_tools.webanno_tsv_reader import read_webanno_tsv, Annotation, Token, AnnotationLink, Document

DATA_DIR = "data/inception_output"


@dataclass
class TokenContext:
    token_annotations: list[dict[str, any]]
    word_annotations: list[dict[str, any]]
    token_idx: dict[str, any]


@logger.catch
def main(iiif_mapping_file: str, textrepo_base_uri: str, data_dir: str):
    webannotation_factory = gt.WebAnnotationFactory(iiif_mapping_file, textrepo_base_uri=textrepo_base_uri)
    annotations = create_web_annotations(webannotation_factory, data_dir)
    print(json.dumps(annotations, indent=2))


def create_web_annotations(webannotation_factory: gt.WebAnnotationFactory, data_dir: str):
    annotations = []
    for p in web_anno_file_paths(data_dir):
        logger.info(f"parsing {p}...")
        annotations.extend(extract_annotations(p, webannotation_factory))
    return annotations


def web_anno_file_paths(directory: str) -> list[str]:
    return glob.glob(f"{directory}/*.tsv")


def extract_annotations(path: str, webannotation_factory: gt.WebAnnotationFactory) -> list[dict[str, any]]:
    doc_id = path.split('/')[-1].replace('.tsv', '')

    word_annotations, token_annotations = load_word_and_token_annotations(doc_id)

    doc = read_webanno_tsv(path)

    tokens = doc.tokens
    wat_annotations = doc.annotations

    whole_tokens = [t for t in tokens if "." not in t.token_num]
    token_idx = {token_id(t): i for i, t in enumerate(whole_tokens)}

    token_context = TokenContext(token_annotations=token_annotations, word_annotations=word_annotations,
                                 token_idx=token_idx)

    event_anno_list = [a for a in wat_annotations
                       if a.layer == EVENT_LAYER_NAME]
    web_annotations = convert_event_annotations(
        annotations=event_anno_list,
        token_context=token_context,
        webannotation_factory=webannotation_factory,
        doc=doc
    )

    entity_webanno_list = [a for a in wat_annotations if
                           a.layer == NAMED_ENTITY_LAYER_NAME]
    # ic(entity_webanno)

    # web_annotations.extend(
    #     convert_entity_annotations(entity_webanno_list, token_context,
    #                                webannotation_factory)
    # )
    web_annotations = convert_entity_annotations(entity_webanno_list, token_context,
                                                 webannotation_factory)

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


def token_id(token: Token) -> str:
    return f"{token.sentence_num}-{token.token_num}"


def convert_event_annotations(annotations, token_context: TokenContext,
                              webannotation_factory: gt.WebAnnotationFactory, doc: Document):
    w3c_annotations = []
    for anno in annotations:
        body_id = f"urn:globalise:event:{uuid.uuid4()}"
        argument_source = {}
        for annotation_link in anno.linked_annotations:
            event_argument_anno = make_event_argument_annotation(
                al=annotation_link,
                linked_annotation=doc.get_annotation_by_id(annotation_link.annotation_id),
                token_context=token_context,
                webannotation_factory=webannotation_factory,
                event_body_id=body_id)
            w3c_annotations.append(event_argument_anno)
            argument_source[annotation_link.annotation_id] = event_argument_anno["body"]["id"]
        body = make_event_body(anno, argument_source, body_id)
        targets = make_targets(anno, token_context, webannotation_factory)

        w3c_anno = {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "id": f"urn:globalise:annotation:{uuid.uuid4()}",
            "type": "Annotation",
            "motivation": "linking",
            "generated": datetime.today().isoformat(),
            "body": body,
            "target": targets
        }
        w3c_annotations.append(w3c_anno)
    return w3c_annotations


def make_event_argument_annotation(al: AnnotationLink,
                                   linked_annotation: Annotation,
                                   token_context: TokenContext,
                                   webannotation_factory,
                                   event_body_id: str):
    anno = linked_annotation
    body = {
        "@context": {"tt": "https://knaw-huc.github.io/ns/team-text#"},
        "type": "tt:EventArgument",
        "id": f"urn:globalise:event_argument:{uuid.uuid4()}",
        "text": anno.text,
        "role": al.label,
        "event": event_body_id
    }
    targets = make_targets(anno, token_context, webannotation_factory)
    w3c_anno = {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "id": f"urn:globalise:annotation:{uuid.uuid4()}",
        "type": "Annotation",
        "motivation": "tagging",
        "generated": datetime.today().isoformat(),
        "body": body,
        "target": targets
    }
    return w3c_anno


def make_event_body(anno: Annotation, argument_source: dict[str, str], body_id: str) -> dict[str, any]:
    fields = anno.features
    body = {
        "@context": {"tt": "https://knaw-huc.github.io/ns/team-text#"},
        "type": "tt:Event",
        "id": body_id,
        "text": anno.text
    }
    if "category" in fields:
        body["category"] = fields["category"]
    if "relationtype" in fields:
        body["relationType"] = fields["relationtype"]
    if anno.linked_annotations:
        arguments = []
        for al in anno.linked_annotations:
            arguments.append(
                {
                    "role": al.label,
                    "source": argument_source[al.annotation_id]
                }
            )
        body["arguments"] = arguments
    return body


def convert_entity_annotations(annotations, token_context: TokenContext,
                               webannotation_factory: gt.WebAnnotationFactory):
    w3c_annotations = []
    for anno in annotations:
        body = make_entity_body(anno)
        if body:
            targets = make_targets(anno, token_context, webannotation_factory)

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


def make_entity_body(anno: Annotation):
    fields = anno.features
    if "value" not in fields:
        logger.warning(f"no 'value' feature in {anno}")
        return {}
    class_name = fields["value"]
    e_uuid = uuid.uuid4()
    body = {
        "@context": {"tt": "https://knaw-huc.github.io/ns/team-text#"},
        "type": "tt:Entity",
        "id": f"urn:globalise:entity:{e_uuid}",
        "class_name": class_name,
        "class_description": ENTITIES[class_name],
        "text": anno.text
    }
    if "identifier" in fields:
        body["url"] = fields["identifier"]
    return body


def make_targets(annotation: Annotation, token_context: TokenContext,
                 webannotation_factory: gt.WebAnnotationFactory):
    targets = []
    relevant_word_annotation_dicts = []
    for t in annotation.tokens:
        i = token_context.token_idx[token_id(t).split('.')[0]]
        token_annotation = token_context.token_annotations[i]
        token_range_begin = token_annotation["offset"]
        token_range_end = token_range_begin + token_annotation["length"]
        relevant_word_annotation_dicts.extend(
            [a for a in token_context.word_annotations
             if word_annotation_covers_token_range(a, token_range_begin, token_range_end)]
        )
    ordered_dicts = deduplicate(relevant_word_annotation_dicts)
    for wa in [annotation_from_dict(d) for d in ordered_dicts]:
        t = webannotation_factory.annotation_targets(wa)
        targets.extend(t)
    return targets


def deduplicate(dicts: list[dict]) -> list[dict]:
    done = set()
    anno_list = []
    for d in sorted(dicts, key=lambda _dict: _dict["id"]):
        if d["id"] not in done:
            done.add(d["id"])
            anno_list.append(d)
    return anno_list


def annotation_from_dict(wa: dict) -> gt.Annotation:
    anno = gt.Annotation.from_dict(wa)
    # convert Coords manually
    anno.metadata["coords"] = [Coords(points) for points in (anno.metadata["coords"])]
    return anno


# def simplified(targets: list[dict]) -> list[dict]:
#     _simplified = []
#     json_set = set(json.dumps(d) for d in targets)
#     deduplicated = [json.loads(j) for j in json_set]
#     ordered_targets = sorted(deduplicated, key=lambda t: t["type"])
#     for key, group in groupby(ordered_targets, key=lambda t: t["type"]):
#         _simplified.extend(group)
#     return _simplified


def word_annotation_covers_token_range(annotation: dict[str, any],
                                       token_range_begin: int,
                                       token_range_end: int) -> bool:
    annotation_range_begin = annotation["offset"]
    annotation_range_end = annotation_range_begin + annotation["length"]
    return token_range_begin >= annotation_range_begin and token_range_end <= annotation_range_end


if __name__ == '__main__':
    main('data/iiif-url-mapping.csv', 'https://globalise.tt.di.huc.knaw.nl/textrepo', DATA_DIR)
