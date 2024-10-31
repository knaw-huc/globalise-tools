#!/usr/bin/env python3
import argparse
import csv
import itertools
import json
import os
from typing import AnyStr, Tuple

import pagexml.parser as pxp
import spacy
from icecream import ic
from loguru import logger
from pagexml.model.physical_document_model import PageXMLScan

import globalise_tools.tools as gt
from globalise_tools.model import TRVersions, GTToken, WebAnnotation, AnnotationEncoder

spacy_core = "nl_core_news_lg"

metadata_csv = "data/metadata_1618-1793_2022-08-30.csv"
ground_truth_csv = "data/globalise-word-joins-MH.csv"
textrepo_version_csv = "data/tr-versions.csv"

metadata_records = []
ground_truth = []
tr_versions: dict[str, TRVersions] = {}
nlp = None


def list_pagexml_files(directory: str):
    all_files = os.listdir(directory)
    return sorted([f'{directory}/{f}' for f in all_files if f.endswith(".xml")])


def index_word_ranges(words: list[gt.DisplayWord], word_range_index) -> dict[str, Tuple[int, int]]:
    index = {}
    for w in words:
        (range_start, range_end) = word_range_index[w.id]
        for pw in w.px_words:
            index[pw.id] = (range_start, range_end)
    return index


def process_pagexml(path: str, document_id: str):
    annotations = []
    scan_doc: PageXMLScan = pxp.parse_pagexml_file(path)
    id_prefix = gt.make_id_prefix(scan_doc)

    px_text_regions, px_text_lines, px_words = gt.extract_px_elements(scan_doc)
    id_dispenser = gt.IdDispenser(id_prefix)
    display_words = gt.to_display_words(px_words, id_dispenser)
    text = ''
    display_word_range_idx = {}
    for w in display_words:
        stripped = w.text.strip()
        wa = gt.word_annotation(id_prefix, stripped, text, w)
        annotations.append(wa)
        display_word_range_idx[w.id] = (wa.offset, wa.offset + wa.length)
        text += w.text
    px_word_range_idx = index_word_ranges(display_words, display_word_range_idx)

    paragraphs = [f'{p}\n' for p in text.split("\n")]
    total_size = len("".join(paragraphs))

    page_id = to_base_name(path)
    annotations.append(
        gt.page_annotation(id_prefix, page_id, path, total_size, document_id)
    )

    for text_region in px_text_regions:
        offset = px_word_range_idx[text_region.first_word_id][0]
        last_word_range = px_word_range_idx[text_region.last_word_id]
        length = last_word_range[1] - offset
        annotations.append(
            gt.text_region_annotation(text_region, id_prefix)
        )

    for text_line in px_text_lines:
        offset = px_word_range_idx[text_line.first_word_id][0]
        last_word_range = px_word_range_idx[text_line.last_word_id]
        length = last_word_range[1] - offset
        annotations.append(
            gt.text_line_annotation(text_line, id_prefix, offset, length)
        )
    return paragraphs, annotations, total_size


def to_conll2002(token: str) -> str:
    return "\n" if token in ["", "\n"] else f"{token} O\n"


def as_conll2002(tokens: list[str]) -> list[str]:
    return [to_conll2002(t) for t in tokens]


def export(base_name: AnyStr,
           all_text: list[AnyStr],
           metadata: dict[AnyStr, any],
           tokens: list[GTToken],
           web_annotations: list[WebAnnotation]
           ):
    print(f"{base_name}:")

    file_name = f"{base_name}.txt"
    print(f"exporting text to {file_name}")
    with open(file_name, 'w', encoding='utf-8') as f:
        f.writelines(all_text)

    file_name = f"{base_name}-tokens.json"
    print(f"exporting tokens to {file_name}")
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(tokens, f, indent=2, cls=AnnotationEncoder)

    file_name = f"{base_name}-segmented-text.json"
    print(f"exporting token segments to {file_name}")
    with open(file_name, 'w', encoding='utf-8') as f:
        segments = [t.text_with_ws if t.text_with_ws else "\n" for t in tokens]
        wrapper = {
            "_ordered_segments": segments
        }
        json.dump(wrapper, f, indent=2)

    file_name = f"{base_name}.conll"
    print(f"exporting tokens as CoNLL 2002 to {file_name}")
    token_texts = [t.text for t in tokens]
    with open(file_name, 'w', encoding='utf-8') as f:
        f.writelines(as_conll2002(token_texts))

    metadata_file_name = f"{base_name}-metadata.json"
    print(f"exporting metadata to {metadata_file_name}")
    with open(metadata_file_name, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, cls=AnnotationEncoder)

    file_name = f"{base_name}-web-annotations.json"
    print(f"exporting web annotations to {file_name}")
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(web_annotations, f, indent=2, cls=AnnotationEncoder)

    print()


def to_base_name(path: str) -> str:
    return path.split('/')[-1].replace(".xml", "")


def create_base_name(pagexml_files: list[str]) -> str:
    first = to_base_name(pagexml_files[0])
    last = to_base_name(pagexml_files[-1])
    i = first.rindex("_")
    base = first[0:i]
    first_page = first[i + 1:]
    last_page = last[i + 1:]
    return f"{base}_{first_page}_{last_page}"


def tokenize(all_pars: list[str]) -> (list[str], list[int]):
    tokens = []
    offsets = []
    text = ''.join(all_pars)
    doc = nlp(text)
    for sentence in doc.sents:
        for token in [t for t in sentence if t.text != "\n"]:
            tokens.append(token.text)
            offsets.append(token.idx)
        tokens.append("")
        offsets.append(-1)
    return tokens, offsets


def tokenize_per_paragraph(all_pars: list[str]) -> list[GTToken]:
    tokens = []
    text_offset = 0
    for par in all_pars:
        doc = nlp(par)
        for sentence in doc.sents:
            for token in [t for t in sentence if t.text != "\n"]:
                offset = text_offset + token.idx
                tokens.append(GTToken(token.text, token.text_with_ws, offset))
        tokens.append(GTToken("", "", -1))
        text_offset += len(par)
    return tokens


def read_metadata(basename: str) -> dict[str, str]:
    (_a, _b, index_nr, scan_nr) = basename.split("_")
    scan = int(scan_nr)
    relevant = [r for r in metadata_records if
                r['Indexnr'] == index_nr and int(r['Scan-begin']) <= scan <= int(r['Scan-Eind'])]
    if len(relevant) > 1:
        raise ">1 metadata records relevant"
    else:
        return relevant[0]


def get_page_id(offset: int, length: int, scan_ranges) -> str:
    range_start = offset
    range_end = offset + length
    overlapping_ranges = [sr for sr in scan_ranges.items()
                          if sr[1][0] <= range_start < sr[1][1]]
    if len(overlapping_ranges) == 1:
        return overlapping_ranges[0][0]
    else:
        ic(range_start, range_end, overlapping_ranges)
        return ":placeholder:"


def make_token_annotations(base_name, tokens, scan_ranges):
    annotations = []
    par_offset = 0
    par_length = 0
    par_num = 1
    par_text = ""
    for i, gp_token in enumerate(tokens):
        token = gp_token.text
        par_text += token + " "
        offset = gp_token.offset
        token_is_paragraph_end = offset < 0
        if token_is_paragraph_end:
            page_id = get_page_id(par_offset, par_length, scan_ranges)
            annotations.append(
                gt.paragraph_annotation(base_name, page_id, par_num, par_offset, par_length, par_text.strip()))
            par_offset += par_length
            par_num += 1
            par_text = ""
        else:
            token_length = len(token)
            page_id = get_page_id(offset, token_length, scan_ranges)
            annotations.append(
                gt.token_annotation(base_name=base_name, page_id=page_id, token_num=i, offset=offset,
                                    token_length=token_length, token_text=token, sentence_num=par_num))
            par_length = offset - par_offset + token_length
        # ic(annotations[-1])
    return annotations


def make_web_annotations(annotations: list[gt.Annotation], webannotation_factory: gt.WebAnnotationFactory) \
        -> list[WebAnnotation]:
    return [gt.to_web_annotation(a, webannotation_factory) for a in annotations]


def ranges_per_scan(annotations: list[gt.Annotation]) -> dict[str, Tuple[int, int]]:
    return {
        pa.page_id: (pa.offset, pa.offset + pa.length)
        for pa in annotations
        if pa.type == gt.PAGE_TYPE
    }


def segment_range(tokens: list[GTToken], char_range_begin: int, char_range_end: int):
    begin_idx = 0
    end_idx = 0
    for i, token in enumerate(tokens):
        if -1 < token.offset <= char_range_begin:
            begin_idx = i
        if -1 < token.offset < char_range_end:
            end_idx = i
        elif -1 < token.offset:
            break
    return begin_idx, end_idx


def add_anchor_range(all_annotations: list[gt.Annotation], tokens: list[GTToken]):
    for a in all_annotations:
        char_range_begin = a.offset
        char_range_end = a.offset + a.length
        a.physical_begin_anchor, a.physical_end_anchor = segment_range(tokens, char_range_begin, char_range_end)


def doc_annotation(base_name: str):
    pass


def process_directory_group(document_id: str, directory_group: list[str],
                            webannotation_factory: gt.WebAnnotationFactory):
    pagexml_files = list_pagexml_files_in_group(directory_group)

    base_name = create_base_name(pagexml_files)

    all_annotations, all_pars = process_pagexml_files(pagexml_files, document_id)

    scan_ranges = ranges_per_scan(all_annotations)

    # (tokens, token_offsets) = tokenize(all_pars)
    tokens = tokenize_per_paragraph(all_pars)

    token_annotations = make_token_annotations(base_name, tokens, scan_ranges)
    all_annotations.extend(token_annotations)
    # token_selection = [a for a in all_annotations if a.type == 'tt:Token'][:5]

    add_tr_versions(all_annotations, base_name)
    add_anchor_range(all_annotations, tokens)

    all_annotations.sort(key=lambda a: f"{a.page_id} {a.offset:06d} {(1000 - a.length):06d}")

    # token_selection = [a for a in all_annotations if a.type == 'tt:Token'][:10]
    # ic(token_selection)

    metadata = read_metadata(to_base_name(pagexml_files[0]))
    metadata.update({
        "tanap_vestiging": "Batavia",
        "tanap_jaar": 1684,
        "annotations": all_annotations,
    })
    web_annotations = make_web_annotations(all_annotations, webannotation_factory)
    add_document_web_annotation(all_annotations, base_name, document_id, web_annotations, webannotation_factory)
    export(base_name, all_pars, metadata, tokens, web_annotations)


def add_document_web_annotation(all_annotations, base_name, document_id, web_annotations, webannotation_factory):
    manifest_id = document_id.split('_')[0]
    manifest_url = f"https://broccoli.tt.di.huc.knaw.nl/mock/globalise/manifest-{manifest_id}.json"
    textrepo_base_url = "https://globalise.tt.di.huc.knaw.nl/textrepo"
    segmented_version_id = tr_versions[base_name].segmented
    end_anchor = max([a.physical_end_anchor for a in all_annotations])
    web_annotations.append(WebAnnotation(
        body={
            "id": f"urn:globalise:document:{document_id}",
            "type": "Document",
            "metadata": {
                "document": document_id,
                "manifest": manifest_url
            }
        },
        target=[
            webannotation_factory.physical_text_anchor_selector_target(
                segmented_version_id=segmented_version_id,
                begin_anchor=0, end_anchor=end_anchor
            ),
            webannotation_factory.physical_text_cutout_target(
                segmented_version_id=segmented_version_id,
                begin_anchor=0, end_anchor=end_anchor
            )
        ]
    ))


def list_pagexml_files_in_group(directory_group):
    pagexml_files = []
    for directory in directory_group:
        pagexml_files.extend(list_pagexml_files(directory))
    pagexml_files.sort()
    return pagexml_files


def process_pagexml_files(pagexml_files: list[str], document_id: str):
    all_pars = []
    all_annotations = []
    start_offset = 0
    for f in pagexml_files:
        (paragraphs, annotations, par_length) = process_pagexml(f, document_id)
        all_pars.extend(paragraphs)
        for annotation in annotations:
            annotation.offset += start_offset
            all_annotations.append(annotation)
        start_offset = start_offset + par_length
    return all_annotations, all_pars


def add_tr_versions(all_annotations, external_id):
    for a in all_annotations:
        a.physical_segmented_version_id = tr_versions[external_id].segmented
        a.txt_version_id = tr_versions[external_id].txt


def init_spacy():
    global nlp
    nlp = spacy.load(spacy_core)


def load_metadata():
    print(f"loading {metadata_csv}...", end=' ')
    with open(metadata_csv) as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            metadata_records.append(row)
    print()


def load_ground_truth():
    print(f"loading {ground_truth_csv}...", end=' ')
    records = []
    with open(ground_truth_csv) as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    joined_lines = [(r['scan'], r['line n'], r['line n+1']) for r in records if r['join?'] != '']
    ground_truth.extend(joined_lines)
    print()


def load_tr_versions():
    print(f"loading {textrepo_version_csv}...", end=' ')
    with open(textrepo_version_csv) as f:
        reader = csv.DictReader(f)
        for row in reader:
            tr_versions[row['external_id']] = TRVersions(txt=row['txt_version'], segmented=row['segmented_version'],
                                                         conll=row['conll_version'])
    print()


def get_arguments():
    parser = argparse.ArgumentParser(
        description="Extract text and annotations from all the PageXML in the given directory",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i",
                        "--iiif-mapping-file",
                        required=True,
                        help="The path to the file mapping pagexml id to iiif base url",
                        type=str)
    parser.add_argument("-m",
                        "--merge-sections",
                        required=False,
                        help="Set this to merge sections into one document",
                        action="store_true")
    parser.add_argument("directory",
                        help="A directory containing the PageXML files to extract the text from.",
                        nargs='+',
                        type=str)
    return parser.parse_args()


def process(directories, iiif_mapping_file, merge_sections):
    webannotation_factory = gt.WebAnnotationFactory(iiif_mapping_file)
    init_spacy()
    load_metadata()
    load_ground_truth()
    load_tr_versions()
    if merge_sections:
        def group_id(path):
            return path.rstrip('/').split('/')[-1].split('_')[0]

        groups = itertools.groupby(directories, group_id)
        for group_id, group in groups:
            process_directory_group(group_id, group, webannotation_factory)
    else:
        for d in directories:
            group_id = d.split('/')[-1]
            process_directory_group(group_id, [d], webannotation_factory)


@logger.catch
def main():
    args = get_arguments()
    if args.directory:
        process(args.directory, args.iiif_mapping_file, args.merge_sections)


if __name__ == '__main__':
    main()
