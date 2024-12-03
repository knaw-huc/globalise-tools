#!/usr/bin/env python3

import os
import os.path
import sys
import stam
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

LINE_TYPE_DATA = {
    "set": "globalise",
    "key": "type",
    "value": "line",
}
PAGE_TYPE_DATA = {
    "set": "globalise",
    "key": "type",
    "value": "page",
}
PARAGRAPH_TYPE_DATA = {
    "set": "globalise",
    "key": "type",
    "value": "paragraph",
}

def main():
    parser = ArgumentParser(
        description="Align ",
        formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--coverage', 
                        help="The percentage of characters that has to be correctly covered for an alignment to be made",
                        default=0.85,
                        type=float)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if not os.path.exists("gm-aligned.store.stam.cbor"):
        print("Please first run gt-align-rgp to produce gm-aligned.store.stam.cbor", file=sys.stderr)
        sys.exit(1)

    print("Loading 'paragraph' alignments...",file=sys.stderr)
    store = stam.AnnotationStore(file="gm-aligned.store.stam.cbor")

    print(f"Computing line->page mapping")
    line2page = {}
    for page in store.data(PAGE_TYPE_DATA).annotations():
        for htr_line_textsel in page.related_text(stam.TextSelectionOperator.embeds(), filter=LINE_TYPE_DATA):
            htr_line = next(htr_line_textsel.annotations(LINE_TYPE_DATA))
            line2page[htr_line.id()] = page.id()

    print(f"Gathering data for alignment...", file=sys.stderr)
    align_pairs = []
    metadata = []
    for translation in store.data({
        "set": "https://w3id.org/stam/extensions/stam-translate/",
        "key": "Translation",
        "value": None,
    }).annotations():
        for rgp_paragraph, htr_paragraph in translation.alignments(): #this assumes the only translations in the model are between RGP and HTR paragraphs
            for htr_line_textsel in htr_paragraph.related_text(stam.TextSelectionOperator.embeds(), filter=LINE_TYPE_DATA):
                htr_line = next(htr_line_textsel.annotations(LINE_TYPE_DATA))
                align_pairs.append( (htr_line_textsel, rgp_paragraph)) 
                metadata.append( htr_line.id() )

    print(f"Gathered {len(align_pairs)} lines", file=sys.stderr)

    print(f"Aligning (this may take very long!)...", file=sys.stderr)
    results = store.align_texts(*align_pairs, max_errors=(1.0 - args.coverage), grow=True)

    print("HTR line id\tHTR line\tRGP line\tPage URL")
    for translations, htr_line_id in zip(results, metadata):
        for translation in translations:
            for htr_line, rgp_line in translation.alignments():
                htr_page_id = line2page[htr_line.id()]
                print(f"{htr_line_id}\t{htr_line}\t{rgp_line}\thttps://transcriptions.globalise.huygens.knaw.nl/detail/urn:globalise:{htr_page_id}")

    store.set_filename("gm-aligned-lines.store.stam.cbor")
    store.save()
