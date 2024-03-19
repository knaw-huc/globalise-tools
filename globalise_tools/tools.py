import csv
from dataclasses import dataclass, field
from typing import List, Any, Tuple, Dict, Union

from dataclasses_json import dataclass_json
from loguru import logger
from pagexml.model.physical_document_model import Coords, PageXMLScan, PageXMLTextRegion

from globalise_tools.model import Document, WebAnnotation
from globalise_tools.nav_provider import NavProvider

PAGE_TYPE = "px:Page"


@dataclass_json
@dataclass
class PXTextRegion:
    id: str
    page_id: str
    coords: Coords
    first_line_id: str
    last_line_id: str
    first_word_id: Union[str, None]
    last_word_id: Union[str, None]
    segment_length: int
    structure_type: str
    text: str


@dataclass_json
@dataclass
class PXTextLine:
    id: str
    text_region_id: str
    page_id: str
    coords: Coords
    first_word_id: Union[str, None]
    last_word_id: Union[str, None]
    text: str


@dataclass_json
@dataclass
class PXWord:
    id: str
    line_id: str
    text_region_id: str
    page_id: str
    text: str
    coords: Coords


@dataclass
class DisplayWord:
    id: str
    px_words: List[PXWord]
    text: str


@dataclass_json
@dataclass(eq=True)
class TextSpan:
    offset: int = 0
    length: int = 0
    begin_anchor: int = 0
    end_anchor: int = 0
    char_start: int = None
    char_end_exclusive: int = None
    textrepo_version_id: str = ""


@dataclass_json
@dataclass(eq=True)
class Annotation:
    type: str
    id: str
    page_id: str
    physical_span: TextSpan = TextSpan()
    logical_span: TextSpan = TextSpan()
    # offset: int
    # length: int
    # physical_segmented_version_id: str = ""
    # physical_begin_anchor: int = 0
    # physical_end_anchor: int = 0
    # logical_segmented_version_id: str = ""
    # logical_begin_anchor: int = 0
    # logical_end_anchor: int = 0
    # txt_version_id: str = ""
    # char_start: int = 0
    # char_end: int = 0
    metadata: dict[str, Any] = field(default_factory=dict, hash=False)


class IdDispenser:
    def __init__(self, prefix: str):
        self.prefix = prefix
        self.counter = 0

    def next(self):
        self.counter += 1
        return f"{self.prefix}{self.counter}"


class WebAnnotationFactory:
    ANNO_CONTEXT = "https://knaw-huc.github.io/ns/huc-di-tt.jsonld"

    def __init__(self, iiif_mapping_file: str, textrepo_base_uri: str):
        self.iiif_base_url_idx = {}
        self.textrepo_base_uri = textrepo_base_uri
        self._init_iiif_base_url_idx(iiif_mapping_file)
        self._iiif_mapping_file = iiif_mapping_file

    @logger.catch
    def annotation_targets(self, annotation: Annotation):
        targets = []
        page_id = annotation.page_id
        canvas_url = get_canvas_url(page_id)
        if "coords" in annotation.metadata:
            coords = annotation.metadata["coords"]
            if isinstance(coords, Coords):
                coords = [coords]
            targets.extend(self._make_image_targets(page_id, coords))
            xywh_list = [self._to_xywh(c) for c in coords]
            points = [c.points for c in coords]
            canvas_target = self._canvas_target(canvas_url=canvas_url, xywh_list=xywh_list, coords_list=points)
            targets.append(canvas_target)
        if annotation.type == PAGE_TYPE:
            iiif_base_url = self._get_iiif_base_url(page_id)
            iiif_url = f"{iiif_base_url}/full/max/0/default.jpg"
            targets.extend([
                {
                    "source": iiif_url,
                    "type": "Image"
                },
                {
                    '@context': self.ANNO_CONTEXT,
                    'source': canvas_url,
                    'type': "Canvas",
                }
            ])
        targets.extend(
            self._make_text_targets(annotation=annotation)
        )
        return targets

    @staticmethod
    def _to_xywh(coords: Coords):
        return f"{coords.left},{coords.top},{coords.width},{coords.height}"

    def _init_iiif_base_url_idx(self, path: str):
        logger.info(f"<= {path}...")
        with open(path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.iiif_base_url_idx[row["pagexml_id"]] = row["iiif_base_url"]
        logger.info("... done")

    def _make_image_targets(self, page_id: str, coords: List[Coords]) -> List[Dict[str, Any]]:
        targets = []
        iiif_base_url = self._get_iiif_base_url(page_id)
        iiif_url = f"{iiif_base_url}/full/max/0/default.jpg"
        selectors = []
        for c in coords:
            xywh = f"{c.box['x']},{c.box['y']},{c.box['w']},{c.box['h']}"
            selector = {
                "type": "FragmentSelector",
                "conformsTo": "http://www.w3.org/TR/media-frags/",
                "value": f"xywh={xywh}"
            }
            selectors.append(selector)

            target = {
                "source": f"{iiif_base_url}/{xywh}/max/0/default.jpg",
                "type": "Image"
            }
            targets.append(target)

        svg_target = self._image_target_wth_svg_selector(iiif_url, [c.points for c in coords])
        selectors.append(svg_target['selector'])
        target = {
            "source": iiif_url,
            "type": "Image",
            "selector": selectors
        }
        targets.append(target)

        return targets

    def _get_iiif_base_url(self, page_id: str) -> str:
        if page_id not in self.iiif_base_url_idx:
            logger.error(f"{page_id} not found in {self._iiif_mapping_file}")
        return self.iiif_base_url_idx[page_id]

    def _make_text_targets(self, annotation: Annotation):
        _physical_text_anchor_selector_target = self.physical_text_anchor_selector_target(annotation.physical_span)
        _physical_cutout_target = self.physical_text_cutout_target(annotation.physical_span)
        _logical_text_anchor_selector_target = self.logical_text_anchor_selector_target(annotation.logical_span)
        _logical_cutout_target = self.logical_text_cutout_target(annotation.logical_span)
        # fragment_selector_target = {
        #     'source': f"{textrepo_base_url}/rest/versions/{annotation.txt_version_id}/contents",
        #     'type': "Text",
        #     "selector": {
        #         "type": "FragmentSelector",
        #         "conformsTo": "http://tools.ietf.org/rfc/rfc5147",
        #         "value": f"char={annotation.char_start},{annotation.char_end}",
        #     }
        # }
        # TODO: move target verification here
        return [_physical_text_anchor_selector_target, _physical_cutout_target,
                _logical_text_anchor_selector_target, _logical_cutout_target]

    def physical_text_anchor_selector_target(self, text_span: TextSpan) -> Dict[str, Any]:
        return self._text_anchor_selector_target("Text", text_span)

    def logical_text_anchor_selector_target(self, text_span: TextSpan) -> Dict[str, Any]:
        return self._text_anchor_selector_target("LogicalText", text_span)

    def _text_anchor_selector_target(self, target_type: str, text_span: TextSpan) -> Dict[str, Any]:
        target = {
            'source': f"{self.textrepo_base_uri}/rest/versions/{text_span.textrepo_version_id}/contents",
            'type': target_type,
            "selector": {
                '@context': self.ANNO_CONTEXT,
                "type": "TextAnchorSelector",
                "start": text_span.begin_anchor,
                "end": text_span.end_anchor
            }
        }
        if text_span.begin_anchor > text_span.end_anchor:
            logger.error(
                f"{target_type}: text_span.begin_anchor {text_span.begin_anchor} > text_span.end_anchor {text_span.end_anchor}")
        if text_span.char_start and text_span.char_end_exclusive:
            target['selector']['charStart'] = text_span.char_start
            target['selector']['charEnd'] = text_span.char_end_exclusive
            if text_span.begin_anchor == text_span.end_anchor and text_span.char_start > text_span.char_end_exclusive + 1:
                logger.error(
                    f"{target_type}: text_span start {text_span.begin_anchor}/{text_span.char_start} > text_span end {text_span.end_anchor}/{text_span.char_end_exclusive}")

        return target

    def physical_text_cutout_target(self, text_span: TextSpan) -> Dict[str, str]:
        return self._text_cutout_target("Text", text_span)

    def logical_text_cutout_target(self, text_span: TextSpan) -> Dict[str, str]:
        return self._text_cutout_target("LogicalText", text_span)

    def _text_cutout_target(self, target_type: str, text_span: TextSpan) -> Dict[str, str]:
        if text_span.char_start and text_span.char_end_exclusive:
            return {
                'source': f"{self.textrepo_base_uri}/view/versions/{text_span.textrepo_version_id}/segments/index/"
                          f"{text_span.begin_anchor}/{text_span.char_start}/{text_span.end_anchor}/{text_span.char_end_exclusive}",
                'type': target_type
            }
        else:
            return {
                'source': f"{self.textrepo_base_uri}/view/versions/{text_span.textrepo_version_id}/segments/"
                          f"index/{text_span.begin_anchor}/{text_span.end_anchor}",
                'type': target_type
            }

    def _canvas_target(self, canvas_url: str, xywh_list: List[str] = None,
                       coords_list: List[List[Tuple[int, int]]] = None) -> dict:
        selectors = []
        if xywh_list:
            for xywh in xywh_list:
                selectors.append({
                    "@context": "http://iiif.io/api/annex/openannotation/context.json",
                    "type": "iiif:ImageApiSelector",
                    "region": xywh
                })
        if coords_list:
            selectors.append(self._svg_selector(coords_list))
        return {
            '@context': self.ANNO_CONTEXT,
            'source': canvas_url,
            'type': "Canvas",
            'selector': selectors
        }

    def _image_target_wth_svg_selector(self, iiif_url: str,
                                       coords_list: List) -> dict:
        return {
            'source': iiif_url,
            'type': "Image",
            'selector': self._svg_selector(coords_list)
        }

    @staticmethod
    def _svg_selector(coords_list):
        path_defs = []
        height = 0
        width = 0
        for coords in coords_list:
            height = max(height, max([c[1] for c in coords]))
            width = max(width, max([c[0] for c in coords]))
            path_def = ' '.join([f"L{c[0]} {c[1]}" for c in coords]) + " Z"
            path_def = 'M' + path_def[1:]
            path_defs.append(path_def)
        path = f"""<path d="{' '.join(path_defs)}"/>"""
        return {
            'type': "SvgSelector",
            'value': f"""<svg height="{height}" width="{width}">{path}</svg>"""
        }


def na_url(file_path):
    file_name = file_path.split('/')[-1]
    file = file_name.replace('.xml', '')
    inv_nr = file_name.split('_')[2]
    return f"https://www.nationaalarchief.nl/onderzoeken/archief/1.04.02/invnr/{inv_nr}/file/{file}"


def tr_url(file_path):
    file_name = file_path.split('/')[-1]
    basename = file_name.replace('.xml', '')
    return f"https://globalise.tt.di.huc.knaw.nl/textrepo/task/find/{basename}/file/contents?type=pagexml"


def in_same_text_line(word: PXWord, next_word: PXWord) -> bool:
    return word.line_id == next_word.line_id


def in_same_text_region(word: PXWord, next_word: PXWord) -> bool:
    return word.text_region_id == next_word.text_region_id


def to_display_words(px_words: List[PXWord], ids: IdDispenser) -> List[DisplayWord]:
    new_words = []
    i = 0
    px_words_len = len(px_words)
    while i < (px_words_len - 1):
        word = px_words[i]
        next_word = px_words[i + 1]
        if not in_same_text_region(word, next_word):
            new_word = DisplayWord(ids.next(), [word], word.text + "\n")
        else:
            if in_same_text_line(word, next_word):
                new_word = DisplayWord(ids.next(), [word], word.text + " ")
            else:
                joined_text = join_words_if_required(word, next_word)
                if joined_text is None:
                    new_word = DisplayWord(ids.next(), [word], word.text + " ")
                else:
                    word_separator = determine_word_separator(i, next_word, px_words, px_words_len)
                    new_word = DisplayWord(ids.next(), [word, next_word], joined_text + word_separator)

        new_words.append(new_word)
        i += len(new_word.px_words)
    if i < px_words_len:
        last_word = px_words[-1]
        new_word = DisplayWord(ids.next(), [last_word], last_word.text)
        new_words.append(new_word)
    return new_words


def determine_word_separator(i, next_word, px_words, px_words_len):
    if (i + 2) >= px_words_len:
        word_separator = ""
    else:
        word3 = px_words[i + 2]
        if in_same_text_region(next_word, word3):
            word_separator = " "
        else:
            word_separator = "\n"
    return word_separator


def join_words_if_required(word, next_word):
    last_char = word.text[-1]
    first_char = next_word.text[0]
    joined_text = None
    if len(word.text) > 1 and len(next_word.text) > 1:
        if word.text[-2:] == "„„" and first_char in ["„", ","]:
            joined_text = word.text[0:-2] + next_word.text[1:]
        elif last_char in ["„", ".", "¬", ",", "="] and first_char in ["„", ","]:
            joined_text = word.text[0:-1] + next_word.text[1:]
        elif last_char not in ["„", "¬"] and first_char in ["„", ","]:
            joined_text = word.text + next_word.text[1:]
        elif last_char in ["„", "¬", "="] and first_char.islower():
            joined_text = word.text[0:-1] + next_word.text
    return joined_text


def generate_word_id(line_id: str, n: int) -> str:
    return f"{line_id}.{n:04d}"


def extract_px_elements(scan_doc: PageXMLScan) -> (List[PXTextRegion], List[PXTextLine], List[PXWord]):
    text_regions = []
    text_lines = []
    px_words = []
    page_id = scan_doc.id.replace(".jpg", "")
    for tr in scan_doc.get_text_regions_in_reading_order():
        collect_elements_from_text_region(tr, page_id, px_words, text_lines, text_regions)
    return text_regions, text_lines, px_words


def collect_elements_from_text_region(tr, page_id, px_words, text_lines, text_regions):
    first_line_index = len(text_lines)
    for line in [line for line in tr.lines if line.text]:
        collect_elements_from_line(line, tr, page_id, px_words, text_lines)
    last_line_index = len(text_lines) - 1
    if first_line_index > last_line_index:
        logger.warning(f"no lines in {tr.id}")
    else:
        first_line_id_in_text_region = text_lines[first_line_index].id
        last_line_id_in_text_region = text_lines[last_line_index].id
        if px_words:
            first_tr_word_index = len(px_words)
            last_tr_word_index = len(px_words) - 1
            first_word_id_in_text_region = px_words[first_tr_word_index].id
            last_word_id_in_text_region = px_words[last_tr_word_index].id
            tr_text = tr.text if tr.text else " ".join(
                [w.text for w in px_words[first_tr_word_index:last_tr_word_index]])
        else:
            first_word_id_in_text_region = None
            last_word_id_in_text_region = None
            tr_text = tr.text if tr.text else " ".join(
                [line.text for line in text_lines[first_line_index:last_line_index]])

        text_regions.append(
            PXTextRegion(id=tr.id,
                         page_id=page_id,
                         coords=tr.coords,
                         first_line_id=first_line_id_in_text_region,
                         last_line_id=last_line_id_in_text_region,
                         first_word_id=first_word_id_in_text_region,
                         last_word_id=last_word_id_in_text_region,
                         segment_length=(last_line_index - first_line_index + 1),
                         text=tr_text,
                         structure_type=tr.type[-1])
        )


def collect_elements_from_line(line, tr, page_id, px_words, text_lines):
    if line.words:
        first_line_word_index = len(px_words)
        for i, w in enumerate(line.words):
            if w.text:
                word_id = w.id if w.id else generate_word_id(line.id, i + 1)
                px_words.append(
                    PXWord(word_id, line.id, tr.id, page_id, w.text, w.coords)
                )
        last_line_word_index = len(px_words) - 1
        first_word_id_in_line = px_words[first_line_word_index].id
        last_word_id_in_line = px_words[last_line_word_index].id
        text_lines.append(
            PXTextLine(id=line.id,
                       text_region_id=tr.id,
                       page_id=page_id,
                       text=line.text,
                       coords=line.coords,
                       first_word_id=first_word_id_in_line,
                       last_word_id=last_word_id_in_line)
        )
    else:
        text_lines.append(
            PXTextLine(id=line.id,
                       text_region_id=tr.id,
                       page_id=page_id,
                       text=line.text,
                       coords=line.coords,
                       first_word_id=None,
                       last_word_id=None)
        )


def get_canvas_url(page_id):
    parts = page_id.split('_')
    inventory_number = parts[-2]
    page_num = int(parts[-1])
    canvas_url = f"https://data.globalise.huygens.knaw.nl/manifests/inventories/{inventory_number}.json/canvas/p{page_num}"
    return canvas_url


def read_missive_metadata(meta_path):
    with open(meta_path) as f:
        reader = csv.DictReader(f)
        documents = [Document.from_dict(d) for d in reader]
    return documents


def make_id_prefix(scan_doc: PageXMLScan) -> str:
    return "urn:globalise:" + scan_doc.id.replace(".jpg", "")


def page_annotation(
        id_prefix: str,
        page_id: str,
        scan_doc_metadata: Dict[str, Any],
        path: str,
        physical_span: TextSpan,
        logical_span: TextSpan,
        document_id: str,
        nav_provider: NavProvider()
) -> Annotation:
    parts = page_id.split("_")
    n = parts[-1]
    inv_nr = parts[-2]
    page_id = ".".join(document_id.split('.')[:-1])  # remove file extension
    externalRef = scan_doc_metadata.get('@externalRef', None)
    metadata = {
        "type": "PageMetadata",
        "document": page_id,
        "file": path,
        "inventoryNumber": inv_nr,
        "n": n,
        "eDepotId": externalRef,
        "creator": scan_doc_metadata['Creator'],
        "created": scan_doc_metadata['Created'],
        "lastChange": scan_doc_metadata['LastChange'],
        "comment": scan_doc_metadata['Comment'],
        "naUrl": na_url(path),
        "trUrl": tr_url(path)
    }
    if not externalRef:
        metadata.pop("eDepotId")
    metadata.update(nav_provider.nav_fields(page_id))
    return Annotation(
        type=PAGE_TYPE,
        id=make_page_id(id_prefix),
        page_id=page_id,
        physical_span=physical_span,
        logical_span=logical_span,
        metadata=metadata
    )


def text_region_annotation(
        text_region: PXTextRegion,
        id_prefix: str,
        physical_span: TextSpan,
        logical_span: TextSpan
) -> Annotation:
    return Annotation(
        type="px:TextRegion",
        id=make_textregion_id(id_prefix, text_region.id),
        page_id=text_region.page_id,
        physical_span=physical_span,
        logical_span=logical_span,
        metadata={
            "type": "TextRegionMetadata",
            "coords": text_region.coords,
            "text": text_region.text,
            "px:structureType": text_region.structure_type,
            "inventoryNumber": (text_region.page_id.split("_")[-2])
        }
    )


def text_line_annotation(
        text_line: PXTextLine,
        id_prefix: str,
        physical_span: TextSpan,
        logical_span: TextSpan
) -> Annotation:
    return Annotation(
        type="px:TextLine",
        id=make_textline_id(id_prefix, text_line.id),
        page_id=text_line.page_id,
        physical_span=physical_span,
        logical_span=logical_span,
        metadata={
            "type": "TextMetadata",
            "text": text_line.text,
            "coords": text_line.coords,
            "inventoryNumber": (text_line.page_id.split("_")[-2])
        }
    )


def word_annotation(id_prefix, stripped, text, w) -> Annotation:
    return Annotation(
        type="tt:Word",
        id=make_word_id(id_prefix, w),
        page_id=w.px_words[0].page_id,
        # offset=len(text),
        # length=len(stripped),
        metadata={
            "type": "WordMetadata",
            "text": stripped,
            "coords": [pxw.coords for pxw in w.px_words]
        }
    )


def paragraph_annotation(base_name: str, page_id: str, par_num: int, par_offset: int, par_length: int, text: str):
    return Annotation(
        type="tt:Paragraph",
        id=f"urn:globalise:{base_name}:paragraph:{par_num}",
        page_id=page_id,
        # offset=par_offset,
        # length=par_length,
        metadata={
            "type": "ParagraphMetadata",
            "text": text
        }
    )


def token_annotation(base_name, page_id, token_num, offset, token_length, token_text, sentence_num: int):
    return Annotation(
        type="tt:Token",
        id=f"urn:globalise:{base_name}:token:{token_num}",
        page_id=page_id,
        # offset=offset,
        # length=token_length,
        metadata={
            "type": "TokenMetadata",
            "text": token_text,
            "sentenceNum": sentence_num,
            "tokenNum": token_num
        }
    )


def make_word_id(prefix: str, w) -> str:
    return prefix + ":word:" + ":".join([pxw.id for pxw in w.px_words])


def make_textline_id(prefix: str, line_id) -> str:
    return prefix + ":textline:" + line_id


def make_page_id(prefix: str) -> str:
    return prefix


def make_textregion_id(prefix: str, textregion_id) -> str:
    return prefix + ":textregion:" + textregion_id


def to_web_annotation(annotation: Annotation, webannotation_factory: WebAnnotationFactory) -> WebAnnotation:
    body = annotation_body(annotation)
    targets = webannotation_factory.annotation_targets(annotation)
    return WebAnnotation(body=body, target=targets)


def annotation_body(annotation: Annotation):
    body = {
        "@context": {"tt": "https://knaw-huc.github.io/ns/team-text#", "px": "https://knaw-huc.github.io/ns/pagexml#"},
        "id": annotation.id,
        "type": annotation.type
    }
    if "text" in annotation.metadata:
        body["text"] = annotation.metadata["text"]
    if annotation.type == PAGE_TYPE:
        body["metadata"] = {
            "document": annotation.metadata["document"],
            "opening": int(annotation.metadata["n"]),
        }
    return body


def is_paragraph(text_region: PageXMLTextRegion) -> bool:
    return text_region_type_is(text_region, "paragraph")


def text_region_type_is(text_region, text_region_type):
    return text_region.type[-1] == text_region_type


def is_marginalia(text_region: PageXMLTextRegion) -> bool:
    return text_region_type_is(text_region, "marginalia")


def is_header(text_region: PageXMLTextRegion) -> bool:
    return text_region_type_is(text_region, "header")


def is_signature(text_region: PageXMLTextRegion) -> bool:
    return text_region_type_is(text_region, "signature-mark")


def paragraph_text(lines: List[str]) -> str:
    if lines:
        break_char1 = "„"
        break_char2 = "¬"
        break_chars = [break_char1, break_char2]
        # ic(lines)
        for i in range(0, len(lines) - 1):
            line0 = lines[i]
            line1 = lines[i + 1]
            if line0[-1] in break_chars:
                lines[i] = line0.rstrip(line0[-1])
                lines[i + 1] = line1.lstrip(break_char1).lstrip(break_char2)
            else:
                lines[i] = f"{line0} "
        # ic(lines)
        return "".join(lines) + "\n"
    else:
        return ""


def print_annotations(cas):
    for a in cas.views[0].get_all_annotations():
        print(a)
        print(f"'{a.get_covered_text()}'")
        print()


def join_words(px_words):
    text = ""
    last_text_region = None
    last_line = None
    for w in px_words:
        if w.text_region_id == last_text_region:
            if w.line_id != last_line:
                text += "|\n"
            text += " "
        else:
            text += "\n\n"
        text += w.text
        last_text_region = w.text_region_id
        last_line = w.line_id
    return text.strip()
