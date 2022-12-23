from dataclasses import dataclass
from itertools import groupby
from typing import List, Dict, Any

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
    tokens: List[Token]
    text: str
    layers: List[Layer]


def process_webanno_tsv_file2(path: str):
    doc = webanno_tsv_read_file(path)
    return extract_annotations(doc)


def extract_annotations(doc) -> List[WebAnno]:
    return [to_web_anno(anno_group, tokens)
            for tokens, anno_group in groupby(doc.annotations, key=lambda a: a.tokens)]


def to_web_anno(anno_group, tokens: List[Token]) -> WebAnno:
    text = " ".join([t.text for t in tokens])
    layers = extract_layers(anno_group)
    return WebAnno(tokens=tokens, text=text, layers=layers)


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
