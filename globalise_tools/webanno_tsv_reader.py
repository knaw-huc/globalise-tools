import itertools
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Sequence

# Strings that need to be escaped with a single backslash according to Webanno Appendix B
RESERVED_STRS = ['\\', '[', ']', '|', '_', '->', ';', '\t', '\n', '*']
SENTENCE_RE = re.compile('^#Text=(.*)')
FIELD_EMPTY_RE = re.compile('^[_*]')
FIELD_WITH_ID_RE = re.compile(r'(.*)\[([0-9]*)]$')
NO_LABEL_ID = -1

# Multiline sentences are split on this character per Webanno Appendix B
MULTILINE_SPLIT_CHAR = '\f'

PREFIX_FORMAT = "#FORMAT="
PREFIX_SPAN_LAYER = "#T_SP="
PREFIX_CHAIN_LAYER = "#T_CH="
PREFIX_RELATION_LAYER = "#T_RL="
PREFIX_TEXT = "#Text="
PREFIX_SENTENCE_ID = "#Sentence.id="
SPAN_LAYER_DEF_RE = re.compile(r'^#T_SP=([^|]+)\|(.*)$')
LINK_FEATURE_NAME = "linked_anno_refs"


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
class AnnotationLink:
    label: str
    annotation_id: str


@dataclass(eq=False)  # Annotations are compared/hashed base on object identity
class Annotation:
    id: str
    tokens: Sequence[Token]
    layer: str
    features: Dict[str, str]
    label_id: int = NO_LABEL_ID
    linked_annotations: list[AnnotationLink] = field(default_factory=list)

    @property
    def start(self):
        return self.tokens[0].start_offset

    @property
    def end(self):
        return self.tokens[-1].end_offset

    @property
    def text(self):
        return ' '.join([t.text for t in self.tokens])

    @property
    def token_texts(self):
        return [token.text for token in self.tokens]


@dataclass
class Document:
    format: str = ""
    layers: List[Layer] = field(default_factory=list)
    sentences: List[Sentence] = field(default_factory=list)
    tokens: List[Token] = field(default_factory=list)
    annotations: List[Annotation] = field(default_factory=list)
    _annotation_idx: Dict[str, Annotation] = field(default_factory=dict)

    def get_annotation_by_id(self, annotation_id: str) -> Annotation:
        annotation_idx = self.__annotation_idx()
        return annotation_idx[annotation_id]

    def __annotation_idx(self):
        if not (self._annotation_idx and len(self._annotation_idx) == len(self.annotations)):
            self._annotation_idx = {a.id: a for a in self.annotations}
        return self._annotation_idx


@dataclass
class ParseContext:
    layer_field_names: List[Tuple[str, str]] = field(default_factory=list)
    multi_token_annotations: Dict[str, Annotation] = field(default_factory=dict)


def read_webanno_tsv(path: str) -> Document:
    """
    Read the webanno_tsv file at `path`
    and return a Document containing the tokens and annotations
    """
    doc = Document()
    with open(path, mode='r', encoding='utf-8') as f:
        lines = f.readlines()

    doc.sentences = [Sentence(idx=i + 1, text=text) for i, text in enumerate(_filter_sentences(lines))]

    context = ParseContext()

    for i, line in enumerate(lines):
        line = _unescape(line.strip())
        if line.startswith(PREFIX_FORMAT):
            doc.format = line.replace(PREFIX_FORMAT, "")
        elif line.startswith(PREFIX_SPAN_LAYER):
            _handle_span_layer(line, doc)
        elif line.startswith(PREFIX_CHAIN_LAYER):
            _todo()glob
        elif line.startswith(PREFIX_RELATION_LAYER):
            _todo()
        elif line.startswith(PREFIX_TEXT):
            pass  # already processed
        elif "\t" in line:
            _handle_annotation_line(line, doc, context)
        elif not line:
            pass  # skip empty lines
        else:
            raise Exception(f"unexpected line at {i + 1} : {line}")
    _process_slot_features(doc)
    return doc


def _todo():
    raise Exception("this function is not implemented yet!")


def _read_span_layer_names(lines: List[str]):
    matches = [SPAN_LAYER_DEF_RE.match(line) for line in lines]
    return [(m.group(1), m.group(2).split('|')) for m in matches if m]


def _annotation_type(layer_name, field_name):
    return '|'.join([layer_name, field_name])


def _unescape(text: str) -> str:
    for s in RESERVED_STRS:
        text = text.replace('\\' + s, s)
    return text


def _handle_annotation_line(line: str, doc: Document, context: ParseContext):
    if not context.layer_field_names:
        context.layer_field_names = _layer_field_names(doc)
    token, raw_feature_values = _parse_line(line)
    raw_feature_value = defaultdict(dict)
    for i, rfv in enumerate(raw_feature_values):
        if rfv not in ["_"]:
            layer_name, field_name = context.layer_field_names[i]
            raw_feature_value[layer_name][field_name] = rfv
    if len(raw_feature_value) > 0:
        # ic(raw_feature_value)
        for layer_name, feature_dict in raw_feature_value.items():
            split_feature_values = _split_dict(feature_dict)
            # ic(split_feature_values)
            for d in split_feature_values:
                features = {}
                label_id = NO_LABEL_ID
                for key, val in d.items():
                    label, label_id = _read_label_and_id(val, key == LINK_FEATURE_NAME)
                    if label:
                        features[key] = label
                multi_token_key = f"{layer_name}/{label_id}"
                annotation_is_multi_token = label_id != NO_LABEL_ID
                if annotation_is_multi_token and multi_token_key in context.multi_token_annotations:
                    annotation = context.multi_token_annotations[multi_token_key]
                    annotation.tokens.append(token)
                else:
                    annotation_id = f"{token.sentence_num}-{token.token_num}"
                    if annotation_is_multi_token:
                        annotation_id += f"[{label_id}]"
                    annotation = Annotation(
                        id=annotation_id,
                        tokens=[token],
                        layer=layer_name,
                        features=features,
                        label_id=label_id
                    )
                    if annotation_is_multi_token:
                        context.multi_token_annotations[multi_token_key] = annotation
                    doc.annotations.append(annotation)
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
                layer_field_names.append((_layer.name, LINK_FEATURE_NAME))
            else:
                raise Exception(f"unexpected feature type: {_feature}")
    return layer_field_names


def _split_dict(d: dict[str, str]) -> List[Dict[str, str]]:
    values = [v.split("|") for v in d.values()]
    max_parts = max(len(v) for v in values)
    return [{k: v[i] for k, v in zip(d.keys(), values)} for i in range(max_parts)]


def _read_label_and_id(feature_value: str, is_slot_feature: bool) -> Tuple[str, int]:
    """
    Reads a Webanno TSV field value, returning a label and an id.
    Returns an empty label for placeholder values '_', '*'
    Examples:
        "OBJ[6]" -> ("OBJ", 6)
        "OBJ"    -> ("OBJ", -1)
        "_"      -> ("", None)
        "*[6]"   -> ("", 6)
    """

    def handle_label(s: str):
        return '' if FIELD_EMPTY_RE.match(s) else _unescape(s)

    match = FIELD_WITH_ID_RE.match(feature_value)
    if match and not is_slot_feature:
        return handle_label(match.group(1)), int(match.group(2))
    else:
        return handle_label(feature_value), NO_LABEL_ID


def _is_slot_feature(f):
    return isinstance(f, SlotFeature)


def _has_slot_feature(layer: Layer):
    return any([_is_slot_feature(f) for f in layer.features])


def _process_slot_features(doc: Document):
    layers_with_slot_features = [_layer.name for _layer in doc.layers if _has_slot_feature(_layer)]
    layer_idx = {_layer.name: _layer for _layer in doc.layers}
    annotations_with_slot_features = [a for a in doc.annotations
                                      if a.layer in layers_with_slot_features]
    slot_features_per_layer = {
        _layer_name: [_feature for _feature in layer_idx[_layer_name].features
                      if _is_slot_feature(_feature)]
        for _layer_name in layers_with_slot_features}
    for a in annotations_with_slot_features:
        slot_features = slot_features_per_layer[a.layer]
        if len(slot_features) > 1:
            raise Exception(f">1 SlotFeature in {a}")
        if LINK_FEATURE_NAME in a.features:
            linked_anno_refs = a.features[LINK_FEATURE_NAME].split(";")
            name = slot_features[0].name
            link_labels = a.features[name].split(";")

            for label, annotation_id in zip(link_labels, linked_anno_refs):
                a.linked_annotations.append(AnnotationLink(label, annotation_id))
            a.features.pop(LINK_FEATURE_NAME)
            a.features.pop(name)
