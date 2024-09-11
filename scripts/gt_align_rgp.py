#!/usr/bin/env python3

#RGP 1-554  -> 1119-0020

#10-992

#RGP deel 10 pagina 857 tot 10 pag 1000 ->  2250-0027 tot 2250-0798
#     1 txt file per pagina uit                 text uit 2250-lines.tsv (paragraph only)
#     globalise-generale-missiven-rgp


# RGP 1-99  -> 1072-881


#   extraheer paragraven met wat body

import os
import csv
import sys
import stam
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


def main():
    parser = ArgumentParser(
        description="Extract texts from RGP data and HTR data",
        formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--metamap',
                        help="CSV file with a metadata mapping between RGP and HTR metadata. This file can be obtained from https://datasets.iisg.amsterdam/file.xhtml?fileId=14452&version=3.0",
                        default="Overzicht van Generale Missiven in 1.04.02 v.3.csv",
                        type=str)
    parser.add_argument('--rgpdir',
                        help="RGP data directory (a git clone of https://github.com/globalise-huygens/globalise-generale-missiven-rgp)",
                        default="globalise-generale-missiven-rgp",
                        type=str)
    parser.add_argument('--htrdir',
                        help="HTR data directory",
                        default=".",
                        type=str)
    args = parser.parse_args()

    with open(args.metamap, mode='r') as file:
        reader_metamap = csv.DictReader(file, delimiter=";",quoting=csv.QUOTE_NONE)
        for row in reader_metamap:
            if row[RGP_DEEL] and row[RGP_PAGINA]:
                rgp_deel = int(row[RGP_DEEL])
                rgp_pagina = int(row[RGP_PAGINA])
                inv_nr = row[INV_NR]
                beginpage = int(row['Beginscan'])
                endpage = int(row['Eindscan'])
                store = stam.AnnotationStore()

                #Load RGP data
                rgp_file = f"{args.rgpdir}/full_volumes/GM_{rgp_deel}.txt"
                lines_text = ""
                id_annotations = []
                print(f"Loading RGP file: {rgp_file}",file=sys.stderr)
                with open(rgp_file,mode="r",encoding="utf-8") as file_rgp:
                    for line in file_rgp:
                        meta, line = line.split("  ", maxsplit=1)
                        page, linenr = meta.split(" ")[1].split(":")
                        page = int(page)
                        linenr = int(linenr)
                        if page >= rgp_pagina:
                            begin = len(lines_text)
                            lines_text += line + "\n"
                            end = len(lines_text)
                            id_annotations.append((f"GM-{rgp_deel}-{page}-{linenr}", page, linenr, begin,end))
                print(f"   found {len(id_annotations)} lines",file=sys.stderr)

                # create a derived plain text resource with all lines in the specified range
                rgp_resource_id = f"GM-{rgp_pagina}+"
                rgp_resource = store.add_resource(id=rgp_resource_id, text=lines_text)

                # associate the RGP page and line number with the line
                for line_id, page, linenr, begin, end in id_annotations:
                    try:
                        store.annotate(id=line_id,target=stam.Selector.textselector(rgp_resource, stam.Offset.simple(begin,end)), data=[
                            LINE_TYPE_DATA,
                            {
                                "set": "globalise",
                                "key": "line",
                                "value": linenr
                            },
                            {
                                "set": "globalise",
                                "key": "page",
                                "value": page,
                            },
                        ])
                    except stam.StamError as e:
                        print("WARNING:", e,file=sys.stderr)

                #Load HTR data
                htr_file = f"{args.htrdir}/{inv_nr}-lines.tsv"
                lines_text = ""
                id_annotations = []
                print(f"Loading HTR file: {htr_file}",file=sys.stderr)
                with open(htr_file, mode='r') as file_inv:
                    reader_inv = csv.DictReader(file_inv, delimiter="\t",quoting=csv.QUOTE_NONE)

                    for row in reader_inv:
                        if row['textregion_type'] == "paragraph":
                            page = int(row['page_no'])
                            if page >= beginpage and page <= endpage:
                                line_text = row['line_text']
                                begin = len(lines_text)
                                lines_text += line_text + "\n"
                                end = len(lines_text)
                                id_annotations.append((row['line_id'],begin,end))
                print(f"   found {len(id_annotations)} lines",file=sys.stderr)

                # create a derived plain text resource with all lines in the specified range
                htr_resource_id = f"NL-HaNA_1.04.02_{inv_nr}_{beginpage}-{endpage}-lines"
                htr_resource = store.add_resource(id=htr_resource_id, text=lines_text)

                # associate the original line IDs with the lines (HTR)
                htr_lines = [ store.annotate(id=line_id,target=stam.Selector.textselector(htr_resource, stam.Offset.simple(begin,end)),data=LINE_TYPE_DATA) for line_id, begin, end in id_annotations ]

                rgp_resource_ts = rgp_resource.textselection(stam.Offset.whole())

                #attempt to align each line from the HTR with the RGP
                for htr_line in htr_lines:
                    htr_line_id = htr_line.id()
                    htr_line_ts = next(htr_line.textselections())
                    transpositions = htr_line_ts.align_text(rgp_resource_ts)
                    print(f"   computed {len(transpositions)} transposition(s)",file=sys.stderr)
                    for transposition in transpositions:
                        for alignment in transposition.alignments():
                            print(htr_line_id,end="")
                            for side in alignment:
                                print(f"\t{side.resource().id()}\t{side.offset()}\t\"{side.text().replace("\"","\\\"")}\"", end="")
                            print(f"\t\"{htr_line_ts.text().replace("\n","\\n").replace("\"","\\\"")}\"")


if __name__ == '__main__':
    main()



