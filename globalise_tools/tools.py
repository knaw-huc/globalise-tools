from dataclasses import dataclass
from typing import List, Dict

from dataclasses_json import dataclass_json
from pagexml.model.physical_document_model import Coords, PageXMLScan


@dataclass_json
@dataclass
class PXTextRegion:
    id: str
    coords: Coords


@dataclass_json
@dataclass
class PXTextLine:
    id: str
    text_region_id: str
    coords: Coords


@dataclass_json
@dataclass
class PXWord:
    id: str
    line_id: str
    text_region_id: str
    text: str
    coords: Coords


@dataclass
class DisplayWord:
    px_words: List[PXWord]
    text: str


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


def to_display_words(px_words: List[PXWord]) -> List[DisplayWord]:
    new_words = []
    i = 0
    px_words_len = len(px_words)
    while i < (px_words_len - 1):
        word = px_words[i]
        next_word = px_words[i + 1]
        if not in_same_text_region(word, next_word):
            new_word = DisplayWord([word], word.text + "\n")
        else:
            if in_same_text_line(word, next_word):
                new_word = DisplayWord([word], word.text + " ")
            else:
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
                if joined_text is None:
                    new_word = DisplayWord([word], word.text + " ")
                else:
                    if (i + 2) >= px_words_len:
                        word_separator = ""
                    else:
                        word3 = px_words[i + 2]
                        if in_same_text_region(next_word, word3):
                            word_separator = " "
                        else:
                            word_separator = "\n"
                    new_word = DisplayWord([word, next_word], joined_text + word_separator)

        new_words.append(new_word)
        i += len(new_word.px_words)
    if i < px_words_len:
        last_word = px_words[-1]
        new_word = DisplayWord([last_word], last_word.text)
        new_words.append(new_word)
    return new_words


def extract_pxwords(scan_doc: PageXMLScan) -> (List[PXWord], Dict[str, PXTextRegion], Dict[str, PXTextLine]):
    text_region_idx = {}
    text_line_idx = {}
    px_words = []
    for tr in scan_doc.get_text_regions_in_reading_order():
        text_region_idx[tr.id] = PXTextRegion(tr.id, tr.coords)
        for l in tr.lines:
            text_line_idx[l.id] = PXTextLine(l.id, tr.id, l.coords)
            for w in l.words:
                if w.text:
                    px_words.append(PXWord(w.id, tr.id, l.id, w.text, w.coords))
    return px_words, text_region_idx, text_line_idx
