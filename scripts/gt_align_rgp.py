#!/usr/bin/env python3

#RGP 1-554  -> 1119-0020

#10-992

#RGP deel 10 pagina 857 tot 10 pag 1000 ->  2250-0027 tot 2250-0798
#     1 txt file per pagina uit                 text uit 2250-lines.tsv (paragraph only)
#     globalise-generale-missiven-rgp


# RGP 1-99  -> 1072-881


#   extraheer paragraven met wat body

import os
import os.path
import csv
import sys
import stam
import math
from collections import defaultdict
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

INV_NR = "Inv.nr. Nationaal Archief (1.04.02)"
RGP_DEEL = "RGP Deel waarin de missive is opgenomen"
RGP_PAGINA = "RGP pagina waarop de missive begint"
LINE_TYPE_DATA = {
    "set": "globalise",
    "key": "type",
    "value": "line",
}
PARAGRAPH_TYPE_DATA = {
    "set": "globalise",
    "key": "type",
    "value": "paragraph",
}
PAGE_TYPE_DATA = {
    "set": "globalise",
    "key": "type",
    "value": "page",
}
LETTER_TYPE_DATA = {
    "set": "globalise",
    "key": "type",
    "value": "letter",
}


def main():
    parser = ArgumentParser(
        description="Extract texts from RGP data and HTR data",
        formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--metamap',
                        help="CSV file with a metadata mapping between RGP and HTR metadata. This file can be obtained from https://datasets.iisg.amsterdam/file.xhtml?fileId=14452&version=3.0",
                        default="Overzicht van Generale Missiven in 1.04.02 v.3.csv",
                        type=str)
    parser.add_argument('--rgpdir',
                        help="Directory containing RGP export from WP6-missieven (a git clone of https://github.com/CLARIAH/wp6-missieven)",
                        default="wp6-missieven",
                        type=str)
    parser.add_argument('--htrdir',
                        help="HTR data directory",
                        default=".",
                        type=str)
    parser.add_argument('--coverage', 
                        help="The percentage of characters that has to be correctly covered for an alignment to be made",
                        default=0.75,
                        type=float)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    print("Loading metadata mapping...",file=sys.stderr)
    rgp2htr_metamap = defaultdict(dict)
    inv_nrs = set()
    with open(args.metamap, mode='r') as file:
        reader_metamap = csv.DictReader(file, delimiter=";",quoting=csv.QUOTE_NONE)
        for row in reader_metamap:
            if row[RGP_DEEL] and row[RGP_PAGINA] and row['Beginscan'] and row['Eindscan']:
                rgp_deel = int(row[RGP_DEEL])
                try:
                    rgp_pagina = int(row[RGP_PAGINA])
                except:
                    print("Skipping invalid page: ", row[RGP_PAGINA],file=sys.stderr)
                    continue
                inv_nr = row[INV_NR] 
                inv_nrs.add(inv_nr)
                htr_beginpage = int(row['Beginscan'])
                htr_endpage = int(row['Eindscan'])

                rgp2htr_metamap[rgp_deel][rgp_pagina] = (inv_nr,htr_beginpage,htr_endpage)

    if os.path.exists("gm-alignment.store.stam.cbor"):
        print("Loading from cache...",file=sys.stderr)
        store = stam.AnnotationStore(file="gm-alignment.store.stam.cbor")
    else:
        #convert RGP data to STAM
        store = stam.AnnotationStore()

        print("Loading RGP text...",file=sys.stderr)
        with open(os.path.join(args.rgpdir,"originals/text.txt"), mode='r', encoding='utf-8') as f:
            text = f.read()
            rgp_resource = store.add_resource(id="RGP", text=text)
            for paragraph in rgp_resource.split_text("\n"):
                store.annotate(target=paragraph.select(), data=PARAGRAPH_TYPE_DATA)

        print("Loading RGP annotations...",file=sys.stderr)
        with open(os.path.join(args.rgpdir,"originals/portions.tsv"), mode='r') as f:
            for row in csv.DictReader(f, delimiter="\t",quoting=csv.QUOTE_NONE):
                portion_text = rgp_resource.textselection(stam.Offset.simple(int(row['start']), int(row['end'])))
                store.annotate(
                    target=portion_text.select(), 
                    data=[ LETTER_TYPE_DATA,
                            {
                                "set": "globalise",
                                "key": "volume",
                                "value": int(row['volume'])
                            },
                            {
                                "set": "globalise",
                                "key": "startpage",
                                "value": int(row['startpage'])
                            },
                            {
                                "set": "globalise",
                                "key": "date",
                                "value": row['date']
                            },
                            {
                                "set": "globalise",
                                "key": "letter",
                                "value": row['letter']
                            },
                            {
                                "set": "globalise",
                                "key": "author",
                                "value": row['author']
                            }
                   ])

        print("Loading HTR data...",file=sys.stderr)
        for inv_nr in sorted(inv_nrs):
            htr_file = f"{args.htrdir}/{inv_nr}-lines.tsv"
            if not os.path.exists(htr_file):
                print("Skipping missing HTR file: ", htr_file,file=sys.stderr)
                continue
            lines_text = ""
            id_annotations = []
            pagebegin = {}
            pageend = {}
            print(f"    {htr_file}",file=sys.stderr)
            with open(htr_file, mode='r') as file_inv:
                reader_inv = csv.DictReader(file_inv, delimiter="\t",quoting=csv.QUOTE_NONE)
                for row in reader_inv:
                    if row['textregion_type'] == "paragraph":
                        page = int(row['page_no'])
                        line_text = row['line_text']
                        begin = len(lines_text)
                        lines_text += line_text + "\n"
                        end = len(lines_text)
                        if not page in pagebegin:
                            pagebegin[page] = begin
                        pageend[page] = end #keeps overwriting
                        id_annotations.append((row['line_id'],begin,end))

                # create a derived plain text resource with all lines in the specified range
                htr_resource_id = f"NL-HaNA_1.04.02_{inv_nr}"
                htr_resource = store.add_resource(id=htr_resource_id, text=lines_text)

                # associate the original line IDs with the lines (HTR)
                htr_lines = [ store.annotate(id=line_id,target=stam.Selector.textselector(htr_resource, stam.Offset.simple(begin,end)),data=LINE_TYPE_DATA) for line_id, begin, end in id_annotations ]

                # associate the page annotations (HTR)
                for (page,begin) in sorted(pagebegin.items()):
                    offset = stam.Offset.simple(begin,pageend[page])
                    store.annotate(id=f"NL-HaNA_1.04.02_{inv_nr}_{page}",data=PAGE_TYPE_DATA, target=htr_resource.textselection(offset).select())

        store.set_filename("gm-alignment.store.stam.cbor")
        store.save()

    VOLUME_KEY = store.key("globalise", "volume")
    STARTPAGE_KEY = store.key("globalise", "startpage")
    LETTER_KEY = store.key("globalise", "letter")

    for rgp_letter in store.data(LETTER_TYPE_DATA).annotations():
        #attempts to align whole letters
        rgp_letter_textsel = next(rgp_letter.textselections())
        #strip the first line (the header)
        try:
            newline = rgp_letter_textsel.find_text("\n",1)[0]
        except IndexError:
            continue
        rgp_letter_textsel = rgp_letter_textsel.resource().textselection(stam.Offset.simple(newline.begin() + 1, rgp_letter_textsel.end()))

        rgp_vol = next(rgp_letter.data(VOLUME_KEY)).value().get()
        letter_id = next(rgp_letter.data(LETTER_KEY)).value().get()
        rgp_startpage = next(rgp_letter.data(STARTPAGE_KEY)).value().get()
        try:
            inv_nr,htr_beginpage, htr_endpage = rgp2htr_metamap[rgp_vol][rgp_startpage]
        except KeyError:
            print(f"No match for letter {letter_id} from RGP vol {rgp_vol} page >= {rgp_startpage}")
            continue
        max_errors = math.ceil(len(rgp_letter_textsel) * (1.0-args.coverage))
        print(f"Aligning letter {letter_id} from RGP vol {rgp_vol} page >= {rgp_startpage} with inv_nr {inv_nr} scans {htr_beginpage}-{htr_endpage} (max_errors={max_errors})...")

        htr_resource_id = f"NL-HaNA_1.04.02_{inv_nr}"
        #TODO: constrain by page range rather than using the whole offset
        htr_resource = store.resource(htr_resource_id).textselection(stam.Offset.whole())
        translations = rgp_letter_textsel.align_text(htr_resource,max_errors=max_errors,grow=True)
        print(f"   computed {len(translations)} translation(s)",file=sys.stderr)
        if args.verbose:
            print(f"<<<<<<< RGP {rgp_vol} {rgp_startpage} {letter_id} {rgp_letter_textsel.offset()}",file=sys.stderr)
            print(rgp_letter_textsel,file=sys.stderr)
        for translation in translations:
            begin = None
            end = None
            for alignment in translation.alignments():
                _,htr_found = alignment
                if args.verbose:
                    print(f">>>>>>>> HTR {htr_resource_id} {htr_found.offset()}",file=sys.stderr)
                    print(htr_found, file=sys.stderr)
                print(f"{rgp_vol}\t{rgp_startpage}\t{letter_id}\t{rgp_letter_textsel.offset()}\t{htr_resource_id}\t{htr_found.offset()}")
        if args.verbose:
            print("------------------------",file=sys.stderr)

if __name__ == '__main__':
    main()
