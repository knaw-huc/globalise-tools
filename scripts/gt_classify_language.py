#!/usr/bin/env python3

import os
import csv
import sys
from collections import Counter
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

#order matters in case of ties in lines, first match wins
LANGS = ('nl_voc','nl','fr','la','en','de','it','pt','es','id','da')
LANGS3 = ('nld_voc','nld','fra','lat','eng','deu','ita','por','spa','msa','dan')
#^-- make sure these match up exactly or things will go wrong

def to_iso639_3(lang):
    if lang == "unknown":
        return lang
    for (lang1,lang3) in zip(LANGS, LANGS3):
        if lang1 == lang:
            return lang3
    raise Exception(f"Invalid language: {lang}")


def classify_line_language(row: dict) -> str:
    if count_alphabetic(row['line_text']) <= 6:
        #too short to classify
        return "unknown"

    confidence_charmodel = float(row['confidence'])
    lang_charmodel = row['lang']

    lex_score = 0
    for lang in LANGS:
        score = float(row[lang])
        if score > lex_score and score > 0:
            lex_score = score

    #if multiple languages are tied for the lexicon, we list them all
    lang_lex = []
    if lex_score > 0:
        for lang in LANGS:
            if float(row[lang]) == lex_score and lang[:2] not in lang_lex:
                lang_lex.append(lang[:2])

    if lang_charmodel in lang_lex and confidence_charmodel >= 0.5:
        #easiest case, models are in agreement
        return lang_charmodel
    elif "nl" in lang_lex and lex_score >= 0.5:
        #lexical says this is dutch, character model thinks otherwise
        return "nl"
    elif lang_charmodel == "nl" and lex_score <= 0.5:
        #character model says this is dutch, lexical model thinks otherwise but  not sufficient confidence
        return lang_charmodel
    elif "nl" not in lang_lex and ' ' not in row['line_text']:
        #this is just a single non-dutch word, refuse to classify as non-dutch
        return "unknown"
    elif confidence_charmodel >= 0.9 and confidence_charmodel > lex_score:
        #character model has very high confidence
        return lang_charmodel
    elif lex_score >= 0.5 and lex_score >= confidence_charmodel:
        #favour lexical model
        return lang_lex[0]
    else:
        #give up
        return "unknown"

def classify_region_language(line_langs: Counter) -> list:
    region_langs = []
    linecount = line_langs.total()
    for lang, count in line_langs.items():
        freq = count / linecount
        if (lang == 'nl' or count >= 3) and freq >= 0.25 and lang != 'unknown':
            region_langs.append(lang)
    return region_langs

def count_alphabetic(s: str):
    return sum(( c.isalpha() for c in s ))

def print_langs(inv_nr, page_no, textregion_id, textregion_type, line_id, page_langs: list, text: str):
    if page_langs:
        langs = ",".join(sorted((to_iso639_3(l) for l in page_langs)))
    else:
        langs = "unknown"
    print(f"{inv_nr}\t{page_no}\t{textregion_id}\t{textregion_type}\t{line_id}\t{langs}\t{text}")

def main():
    parser = ArgumentParser(
        description="Extract line text from pagexml files",
        formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('inputfiles',
                        nargs='+',
                        help="TSV file with language classifier output per line (*-lines.lang.tsv)",
                        type=str)
    args = parser.parse_args()


    print("inv_nr\tpage_no\ttextregion_id\ttextregion_type\tline_id\tlangs\tline_text")

    for filename in args.inputfiles:
        prev = (None,None,None,None)
        line_langs = Counter() 
        page_langs = []
        with open(filename, mode='r') as file:
            reader = csv.DictReader(file, delimiter="\t",quoting=csv.QUOTE_NONE)
            for row in reader:
                current = (row['inv_nr'],row['page_no'],row['textregion_id'], row['textregion_type'])
                if current != prev:
                    region_langs = classify_region_language(line_langs)
                    for lang in region_langs:
                        if lang not in page_langs:
                            page_langs.append(lang)
                    inv_nr, page_no, textregion_id, textregion_type = prev
                    if inv_nr:
                        print_langs(inv_nr, page_no,textregion_id, textregion_type, "",region_langs,"")
                    line_langs.clear();
                if current[0:2] != prev[:2]:
                    #new page
                    inv_nr, page_no = prev[:2]
                    if inv_nr:
                        print_langs(inv_nr, page_no, "", "", "", page_langs,"")
                        page_langs.clear()
                if row['textregion_type'] == 'paragraph':
                    lang = classify_line_language(row)
                    line_langs[lang] += 1
                    print_langs(row['inv_nr'], row['page_no'],row['textregion_id'], row['textregion_type'], row['line_id'],[lang],row['line_text'])
                prev = current
            
            #wrap up after last one
            inv_nr, page_no, textregion_id, textregion_type = prev
            if inv_nr:
                region_langs = classify_region_language(line_langs)
                for lang in region_langs:
                    if lang not in page_langs:
                        page_langs.append(lang)
                print_langs(inv_nr, page_no,"", "", "",page_langs,"")


if __name__ == '__main__':
    main()


