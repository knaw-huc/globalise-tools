from dataclasses import dataclass
from itertools import groupby
from typing import List, Dict, Any

from icecream import ic
from webanno_tsv import webanno_tsv_read_file, Token


@dataclass
class LayerElement:
    id: str
    fields: Dict[str, Any]


@dataclass
class Layer:
    label: str
    elements: List[LayerElement]


@dataclass
class WebAnno:
    token_idxs: List[int]
    text: str
    layers: List[Layer]


def token_identifier(token: Token):
    return f"{token.sentence_idx}-{token.idx}"


def process_webanno_tsv_file2(path: str) -> (List[Token], List[WebAnno]):
    doc = webanno_tsv_read_file(path)
    tokens = doc.tokens
    ic(tokens)
    token_idx = {token_identifier(token): i for i, token in enumerate(tokens)}
    return tokens, extract_annotations(doc, token_idx)


def extract_annotations(doc, token_idx: Dict[str, int]) -> List[WebAnno]:
    return [to_web_anno(anno_group, tokens, token_idx)
            for tokens, anno_group in groupby(doc.annotations, key=lambda a: a.tokens)]


def to_web_anno(anno_group, tokens: List[Token], token_idx: Dict[str, int]) -> WebAnno:
    text = " ".join([t.text for t in tokens])
    layers = extract_layers(anno_group)
    token_idxs = [token_idx[token_identifier(t)] for t in tokens]
    return WebAnno(token_idxs=token_idxs, text=text, layers=layers)


def extract_layers(annotations) -> List[Layer]:
    sorted_by_layer = sorted(annotations, key=lambda a: a.layer)
    return [to_layer(anno_group, layer_label)
            for layer_label, anno_group in groupby(sorted_by_layer, key=lambda a: a.layer)]


def to_layer(anno_group, layer_label) -> Layer:
    elements = extract_elements(anno_group)
    return Layer(label=layer_label, elements=elements)


def extract_elements(annotations) -> List[LayerElement]:
    elements = []
    sorted_by_label_id = sorted(annotations, key=lambda a: a.label_id)
    for element_id, annotation_group in groupby(sorted_by_label_id, key=lambda a: a.label_id):
        fields = {}
        for a in annotation_group:
            fields[a.field] = a.label
        elements.append(LayerElement(id=element_id, fields=fields))
    return elements
