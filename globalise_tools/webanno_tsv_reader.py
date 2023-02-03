import itertools
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Any

from icecream import ic

# Strings that need to be escaped with a single backslash according to Webanno Appendix B
RESERVED_STRS = ['\\', '[', ']', '|', '_', '->', ';', '\t', '\n', '*']
SENTENCE_RE = re.compile('^#Text=(.*)')

# Mulitiline sentences are split on this character per Webanno Appendix B
MULTILINE_SPLIT_CHAR = '\f'

PREFIX_FORMAT = "#FORMAT="
PREFIX_SPAN_LAYER = "#T_SP="
PREFIX_CHAIN_LAYER = "#T_CH="
PREFIX_RELATION_LAYER = "#T_RL="
PREFIX_TEXT = "#Text="
PREFIX_SENTENCE_ID = "#Sentence.id="
SPAN_LAYER_DEF_RE = re.compile(r'^#T_SP=([^|]+)\|(.*)$')


@dataclass
class Feature:
    name: str


@dataclass
class SimpleFeature(Feature):
    name: str


@dataclass
class SlotFeature(Feature):
    name: str
    link_layer_name: str


@dataclass
class Layer:
    name: str = ""
    features: List[Feature] = field(default_factory=list)


@dataclass()
class Sentence:
    idx: int
    text: str


@dataclass
class Token:
    sentence_num: int
    token_num: str
    start_offset: int
    end_offset: int
    text: str


@dataclass
class Document:
    format: str = ""
    layers: List[Layer] = field(default_factory=list)
    sentences: List[Sentence] = field(default_factory=list)
    tokens: List[Token] = field(default_factory=list)


def read_webanno_tsv(path: str) -> Document:
    doc = Document()
    with open(path, mode='r', encoding='utf-8') as f:
        lines = f.readlines()

    sentence_strs = _filter_sentences(lines)
    doc.sentences = [Sentence(idx=i + 1, text=text) for i, text in enumerate(sentence_strs)]

    layer_defs = _read_span_layer_names(lines)
    ic(layer_defs)

    context = {}

    for i, line in enumerate(lines):
        line = _unescape(line.strip())
        if line.startswith(PREFIX_FORMAT):
            doc.format = line.replace(PREFIX_FORMAT, "")
        elif line.startswith(PREFIX_SPAN_LAYER):
            _handle_span_layer(line, doc)
        elif line.startswith(PREFIX_CHAIN_LAYER):
            pass
        elif line.startswith(PREFIX_RELATION_LAYER):
            pass
        elif line.startswith(PREFIX_TEXT):
            pass
        elif "\t" in line:
            _handle_annotation_line(line, doc, context)
        elif not line:
            pass
        else:
            raise Exception(f"unexpected line at {i + 1} : {line}")
    return doc


def _read_span_layer_names(lines: List[str]):
    matches = [SPAN_LAYER_DEF_RE.match(line) for line in lines]
    return [(m.group(1), m.group(2).split('|')) for m in matches if m]


def _annotation_type(layer_name, field_name):
    return '|'.join([layer_name, field_name])


def _unescape(text: str) -> str:
    for s in RESERVED_STRS:
        text = text.replace('\\' + s, s)
    return text


def _handle_annotation_line(line: str, doc: Document, context: Dict[str, Any]):
    if "layer_field_names" not in context:
        context["layer_field_names"] = _layer_field_names(doc)
    token, raw_feature_values = _parse_line(line)
    raw_feature_value = defaultdict(dict)
    for i, rfv in enumerate(raw_feature_values):
        if rfv not in ["_", "*"]:
            layer_name, field_name = context["layer_field_names"][i]
            raw_feature_value[layer_name][field_name] = rfv
    if len(raw_feature_value) > 0:
        ic(raw_feature_value)
        for layer_name, feature_dict in raw_feature_value.items():
            split_feature_values = _split_dict(feature_dict)
            ic(split_feature_values)
    doc.tokens.append(token)


def _parse_line(line):
    parts = line.split("\t")
    (sentence_num, token_num) = parts[0].split("-")
    (start_offset, end_offset) = parts[1].split("-")
    value = parts[2]
    token = Token(
        sentence_num=int(sentence_num),
        token_num=token_num,
        start_offset=int(start_offset),
        end_offset=int(end_offset),
        text=value,
    )

    raw_feature_values = parts[3:]
    return token, raw_feature_values


def _filter_sentences(lines: List[str]) -> List[str]:
    """
    Filter lines beginning with 'Text=', if multiple such lines are
    following each other, concatenate them.
    """
    matches = [SENTENCE_RE.match(line) for line in lines]
    match_groups = [list(ms) for is_m, ms in itertools.groupby(matches, key=lambda m: m is not None) if is_m]
    text_groups = [[m.group(1) for m in group] for group in match_groups]
    return [MULTILINE_SPLIT_CHAR.join(group) for group in text_groups]


# def _handle_sentence_text(line, doc):
#     sentence = line.replace(PREFIX_TEXT, "")
#     doc.sentences.append(sentence)


def _handle_span_layer(line: str, doc: Document):
    parts = line.replace(PREFIX_SPAN_LAYER, "").split('|')
    features = []
    i = 1
    while i < len(parts):
        part = parts[i]
        if not part:
            features.append(SimpleFeature(name="value"))
        elif not part.startswith("ROLE_"):
            features.append(SimpleFeature(name=part))
        else:
            fparts = part.split("_")
            name = fparts[1].split(':')[1]
            link_layer_name = parts[i + 1]
            features.append(SlotFeature(name=name, link_layer_name=link_layer_name))
            i += 1
        i += 1
    doc.layers.append(Layer(name=(parts[0]), features=features))


def _layer_field_names(doc):
    layer_field_names = []
    for _layer in doc.layers:
        for _feature in _layer.features:
            if isinstance(_feature, SimpleFeature):
                layer_field_names.append((_layer.name, _feature.name))
            elif isinstance(_feature, SlotFeature):
                layer_field_names.append((_layer.name, _feature.name))
                layer_field_names.append((_layer.name, "linked_anno_refs"))
            else:
                raise Exception(f"unexpected feature type: {_feature}")
    return layer_field_names


def _split_dict(d: dict[str, str]) -> List[Dict[str, str]]:
    _list = []
    d2 = {}
    number_of_parts = 1
    for key, value in d.items():
        values = value.split("|")
        d2[key] = values
        number_of_parts = len(values)
    for i in range(number_of_parts):
        d3 = {}
        for key, values in d2.items():
            d3[key] = values[i]
        _list.append(d3)
    return _list
