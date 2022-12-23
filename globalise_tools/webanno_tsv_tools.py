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
    wat_annotations = []
    for tokens, g in groupby(doc.annotations, key=lambda a: a.tokens):
        text = " ".join([t.text for t in tokens])
        layers = []
        for layer_label, ag in groupby(g, key=lambda a: a.layer):
            elements = []
            sorted_by_label_id = sorted(ag, key=lambda a: a.label_id)
            for element_id, le_group in groupby(sorted_by_label_id, key=lambda a: a.label_id):
                fields = {}
                for a in le_group:
                    fields[a.field] = a.label
                elements.append(LayerElement(id=element_id, fields=fields))
            layers.append(Layer(label=layer_label, elements=elements))
        wat_annotations.append(WebAnno(tokens=tokens, text=text, layers=layers))

    return wat_annotations
