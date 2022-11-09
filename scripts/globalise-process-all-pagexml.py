#!/usr/bin/env python3
from dataclasses import dataclass

from pagexml.model.physical_document_model import Coords
from pagexml.parser import parse_pagexml_file

from globalise_tools.tools import na_url

data_dir = '/Users/bram/workspaces/globalise/globalise-tools/data'

files = [
    '199/NL-HaNA_1.04.02_1297_0019.xml',
    '199/NL-HaNA_1.04.02_1297_0020.xml',
    '199/NL-HaNA_1.04.02_1297_0021.xml',
    '199/NL-HaNA_1.04.02_1297_0022.xml',
    '199/NL-HaNA_1.04.02_1297_0023.xml',
    '199/NL-HaNA_1.04.02_1297_0024.xml',
    '199/NL-HaNA_1.04.02_1297_0025.xml',
    '199/NL-HaNA_1.04.02_1297_0026.xml',
    '199/NL-HaNA_1.04.02_1297_0027.xml',
    '199/NL-HaNA_1.04.02_1297_0028.xml',
    '199/NL-HaNA_1.04.02_1297_0029.xml',
    '199/NL-HaNA_1.04.02_1297_0030.xml',
    '199/NL-HaNA_1.04.02_1297_0031.xml',
    '199/NL-HaNA_1.04.02_1297_0032.xml',
    '199/NL-HaNA_1.04.02_1297_0033.xml',
    '199/NL-HaNA_1.04.02_1297_0034.xml',
    '199/NL-HaNA_1.04.02_1297_0035.xml',
    '199/NL-HaNA_1.04.02_1297_0036.xml',
    '199/NL-HaNA_1.04.02_1297_0037.xml',
    '199/NL-HaNA_1.04.02_1297_0038.xml',
    '199/NL-HaNA_1.04.02_1297_0039.xml',
    '199/NL-HaNA_1.04.02_1297_0040.xml',
    '199/NL-HaNA_1.04.02_1297_0041.xml',
    '199/NL-HaNA_1.04.02_1297_0042.xml',
    '199/NL-HaNA_1.04.02_1297_0043.xml',
    '199/NL-HaNA_1.04.02_1297_0044.xml',
    '199/NL-HaNA_1.04.02_1297_0045.xml',
    '199/NL-HaNA_1.04.02_1297_0046.xml',
    '199/NL-HaNA_1.04.02_1297_0047.xml',
    '199/NL-HaNA_1.04.02_1297_0048.xml',
    '199/NL-HaNA_1.04.02_1297_0049.xml',
    '199/NL-HaNA_1.04.02_1297_0050.xml',
    '199/NL-HaNA_1.04.02_1297_0051.xml',
    '199/NL-HaNA_1.04.02_1297_0052.xml',
    '199/NL-HaNA_1.04.02_1297_0053.xml',
    '199/NL-HaNA_1.04.02_1297_0054.xml',
    '199/NL-HaNA_1.04.02_1297_0055.xml',
    '199/NL-HaNA_1.04.02_1297_0056.xml',
    '199/NL-HaNA_1.04.02_1297_0057.xml',
    '316_1/NL-HaNA_1.04.02_1589_0019.xml',
    '316_1/NL-HaNA_1.04.02_1589_0020.xml',
    '316_1/NL-HaNA_1.04.02_1589_0021.xml',
    '316_2/NL-HaNA_1.04.02_1589_0048.xml',
    '316_2/NL-HaNA_1.04.02_1589_0049.xml',
    '316_3/NL-HaNA_1.04.02_1589_0052.xml',
    '316_3/NL-HaNA_1.04.02_1589_0053.xml',
    '316_3/NL-HaNA_1.04.02_1589_0054.xml',
    '316_3/NL-HaNA_1.04.02_1589_0055.xml',
    '316_3/NL-HaNA_1.04.02_1589_0056.xml',
    '405/NL-HaNA_1.04.02_1859_0115.xml',
    '405/NL-HaNA_1.04.02_1859_0116.xml',
    '405/NL-HaNA_1.04.02_1859_0117.xml',
    '405/NL-HaNA_1.04.02_1859_0118.xml',
    '405/NL-HaNA_1.04.02_1859_0119.xml',
    '405/NL-HaNA_1.04.02_1859_0120.xml',
    '405/NL-HaNA_1.04.02_1859_0121.xml',
    '405/NL-HaNA_1.04.02_1859_0122.xml',
    '405/NL-HaNA_1.04.02_1859_0123.xml',
    '405/NL-HaNA_1.04.02_1859_0124.xml',
    '405/NL-HaNA_1.04.02_1859_0125.xml',
    '405/NL-HaNA_1.04.02_1859_0126.xml',
    '405/NL-HaNA_1.04.02_1859_0127.xml',
    '405/NL-HaNA_1.04.02_1859_0128.xml',
    '405/NL-HaNA_1.04.02_1859_0129.xml',
    '405/NL-HaNA_1.04.02_1859_0130.xml',
    '405/NL-HaNA_1.04.02_1859_0131.xml',
    '405/NL-HaNA_1.04.02_1859_0132.xml',
    '405/NL-HaNA_1.04.02_1859_0133.xml',
    '405/NL-HaNA_1.04.02_1859_0134.xml',
    '405/NL-HaNA_1.04.02_1859_0135.xml',
    '43/NL-HaNA_1.04.02_1092_0017.xml',
    '43/NL-HaNA_1.04.02_1092_0018.xml',
    '43/NL-HaNA_1.04.02_1092_0019.xml',
    '43/NL-HaNA_1.04.02_1092_0020.xml',
    '43/NL-HaNA_1.04.02_1092_0021.xml',
    '685_1/NL-HaNA_1.04.02_7573_0077.xml',
    '685_1/NL-HaNA_1.04.02_7573_0078.xml',
    '685_2/NL-HaNA_1.04.02_7573_0183.xml',
    '685_2/NL-HaNA_1.04.02_7573_0184.xml',
    '685_2/NL-HaNA_1.04.02_7573_0185.xml',
    '685_2/NL-HaNA_1.04.02_7573_0186.xml',
    '685_2/NL-HaNA_1.04.02_7573_0187.xml',
    '685_2/NL-HaNA_1.04.02_7573_0188.xml',
    '685_2/NL-HaNA_1.04.02_7573_0189.xml',
    '685_2/NL-HaNA_1.04.02_7573_0190.xml',
]


@dataclass
class PXWord:
    text_region_id: str
    line_id: str
    text: str
    coords: Coords


def print_paragraphs(file_path: str):
    scan_doc = parse_pagexml_file(f"{data_dir}/{file_path}")

    pxwords = []
    for tr in scan_doc.get_text_regions_in_reading_order():
        for l in tr.lines:
            for w in l.words:
                if w.text:
                    pxwords.append(PXWord(tr.id, l.id, w.text, w.coords))

    text = join_words(pxwords)

    print("[LINES]\n")
    print(text)

    print("-" * 80)

    print("[JOINED]\n")
    joined = text.replace(".|\n „", "").replace("„|\n „", "").replace("„|\n ", "").replace("|\n ", " ")
    print(joined)


def join_words(pxwords):
    text = ""
    last_text_region = None
    last_line = None
    for w in pxwords:
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


def main():
    for file_path in files:
        print(file_path)
        print(na_url(file_path))
        print("-" * 80)
        print_paragraphs(file_path)
        print()
        print("=-" * 40)
        print()


if __name__ == '__main__':
    main()
