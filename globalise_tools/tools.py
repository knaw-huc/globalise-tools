import csv
from dataclasses import dataclass, field
from typing import List, Any, Tuple, Dict

from dataclasses_json import dataclass_json
from loguru import logger
from pagexml.model.physical_document_model import Coords, PageXMLScan


@dataclass_json
@dataclass
class PXTextRegion:
    id: str
    page_id: str
    coords: Coords
    first_word_id: str
    last_word_id: str
    text: str


@dataclass_json
@dataclass
class PXTextLine:
    id: str
    text_region_id: str
    page_id: str
    coords: Coords
    first_word_id: str
    last_word_id: str
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
class Annotation:
    type: str
    id: str
    page_id: str
    offset: int
    length: int
    segmented_version_id: str = ""
    begin_anchor: int = 0
    end_anchor: int = 0
    txt_version_id: str = ""
    char_start: int = 0
    char_end: int = 0
    metadata: dict[str, Any] = field(default_factory=dict, hash=False)


class IdDispenser:
    def __init__(self, prefix: str):
        self.prefix = prefix
        self.counter = 0

    def next(self):
        self.counter += 1
        return f"{self.prefix}{self.counter}"


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
    first_tr_word_index = len(px_words)
    for line in tr.lines:
        collect_elements_from_line(line, tr, page_id, px_words, text_lines)
    last_tr_word_index = len(px_words) - 1
    first_word_id_in_text_region = px_words[first_tr_word_index].id
    last_word_id_in_text_region = px_words[last_tr_word_index].id
    tr_text = tr.text if tr.text else " ".join([w.text for w in px_words[first_tr_word_index:last_tr_word_index]])
    text_regions.append(
        PXTextRegion(id=tr.id,
                     page_id=page_id,
                     coords=tr.coords,
                     first_word_id=first_word_id_in_text_region,
                     last_word_id=last_word_id_in_text_region,
                     text=tr_text)
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


def cutout_target(textrepo_base_url: str,
                  segmented_version_id: str,
                  begin_anchor: str,
                  end_anchor: str) -> Dict[str, str]:
    return {
        'source': f"{textrepo_base_url}/view/versions/{segmented_version_id}/segments/"
                  f"index/{begin_anchor}/{end_anchor}",
        'type': "Text"
    }


class WebAnnotationFactory:
    REPUBLIC_CONTEXT = "https://brambg.github.io/ns/republic.jsonld"

    def __init__(self, iiif_mapping_file: str):
        self.iiif_base_url_idx = {}
        self._init_iiif_base_url_idx(iiif_mapping_file)

    @logger.catch
    def annotation_targets(self, annotation: Annotation):
        targets = []
        page_id = annotation.page_id
        canvas_url = f"urn:globalise:canvas:{page_id}"
        if "coords" in annotation.metadata:
            coords = annotation.metadata["coords"]
            if isinstance(coords, Coords):
                coords = [coords]
            targets.extend(self._make_image_targets(page_id, coords))
            xywh_list = [self._to_xywh(c) for c in coords]
            points = [c.points for c in coords]
            canvas_target = self._canvas_target(canvas_url=canvas_url, xywh_list=xywh_list, coords_list=points)
            targets.append(canvas_target)
        if annotation.type == "px:Page":
            iiif_base_url = self._get_iiif_base_url(page_id)
            iiif_url = f"{iiif_base_url}/full/max/0/default.jpg"
            targets.extend([
                {
                    "source": iiif_url,
                    "type": "Image"
                },
                {
                    '@context': "https://brambg.github.io/ns/republic.jsonld",
                    'source': canvas_url,
                    'type': "Canvas",
                }
            ])
        targets.extend(
            self._make_text_targets(textrepo_base_url="https://globalise.tt.di.huc.knaw.nl/textrepo",
                                    annotation=annotation)
        )
        return targets

    @staticmethod
    def _to_xywh(coords: Coords):
        return f"{coords.left},{coords.top},{coords.width},{coords.height}"

    def _init_iiif_base_url_idx(self, path: str):
        logger.info(f"loading {path}...")
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
        return self.iiif_base_url_idx[page_id]

    def _make_text_targets(self, textrepo_base_url, annotation: Annotation):
        _text_anchor_selector_target = self.text_anchor_selector_target(textrepo_base_url,
                                                                        annotation.segmented_version_id,
                                                                        annotation.begin_anchor, annotation.end_anchor)
        _cutout_target = cutout_target(textrepo_base_url,
                                       annotation.segmented_version_id,
                                       annotation.begin_anchor,
                                       annotation.end_anchor)
        # fragment_selector_target = {
        #     'source': f"{textrepo_base_url}/rest/versions/{annotation.txt_version_id}/contents",
        #     'type': "Text",
        #     "selector": {
        #         "type": "FragmentSelector",
        #         "conformsTo": "http://tools.ietf.org/rfc/rfc5147",
        #         "value": f"char={annotation.char_start},{annotation.char_end}",
        #     }
        # }
        return [_text_anchor_selector_target, _cutout_target]

    def text_anchor_selector_target(self, textrepo_base_url: str, segmented_version_id: str, begin_anchor: int,
                                    end_anchor: int) -> Dict[str, Any]:
        return {
            'source': f"{textrepo_base_url}/rest/versions/{segmented_version_id}/contents",
            'type': "Text",
            "selector": {
                '@context': self.REPUBLIC_CONTEXT,
                "type": "urn:republic:TextAnchorSelector",
                "start": begin_anchor,
                "end": end_anchor
            }
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
            '@context': "https://brambg.github.io/ns/republic.jsonld",
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
