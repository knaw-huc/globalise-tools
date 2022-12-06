from dataclasses import dataclass
from typing import List

from dataclasses_json import dataclass_json
from pagexml.model.physical_document_model import Coords, PageXMLScan


@dataclass_json
@dataclass
class PXTextRegion:
    id: str
    page_id: str
    coords: Coords
    first_word_id: str
    last_word_id: str


@dataclass_json
@dataclass
class PXTextLine:
    id: str
    text_region_id: str
    page_id: str
    coords: Coords
    first_word_id: str
    last_word_id: str


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
            new_word = DisplayWord(ids.next(),[word], word.text + "\n")
        else:
            if in_same_text_line(word, next_word):
                new_word = DisplayWord(ids.next(),[word], word.text + " ")
            else:
                joined_text = join_words_if_required(word, next_word)
                if joined_text is None:
                    new_word = DisplayWord(ids.next(),[word], word.text + " ")
                else:
                    word_separator = determine_word_separator(i, next_word, px_words, px_words_len)
                    new_word = DisplayWord(ids.next(),[word, next_word], joined_text + word_separator)

        new_words.append(new_word)
        i += len(new_word.px_words)
    if i < px_words_len:
        last_word = px_words[-1]
        new_word = DisplayWord(ids.next(),[last_word], last_word.text)
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
    text_regions.append(
        PXTextRegion(id=tr.id,
                     page_id=page_id,
                     coords=tr.coords,
                     first_word_id=first_word_id_in_text_region,
                     last_word_id=last_word_id_in_text_region)
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
                       coords=line.coords,
                       first_word_id=first_word_id_in_line,
                       last_word_id=last_word_id_in_line)
        )
