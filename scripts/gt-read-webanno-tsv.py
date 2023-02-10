#!/usr/bin/env python3
import argparse

from blessedtable import Blessedtable
from colorama import Fore
from loguru import logger


# data_dir = "data/inception_output"
#
#
# def main():
#     for path in web_anno_file_paths(data_dir):
#         doc_id = make_doc_id(path)
#         word_annotations, token_annotations = load_word_and_token_annotations(doc_id)
#
#         doc = read_webanno_tsv(path)
#         tokens = doc.tokens
#         annotations = doc.annotations
#
#         selection = annotations
#         ic(selection)
#
#         whole_tokens = [t for t in tokens if "." not in t.token_num]
#         token_idx = {token_id(t): i for i, t in enumerate(whole_tokens)}
#
#         for annotation in selection:
#             print(annotation)
#             text1 = annotation.text
#             print(text1)
#             print([f"{t.sentence_num}-{t.token_num} {t.text}" for t in annotation.tokens])
#             ta = [token_annotations[token_idx[token_id(t).split('.')[0]]] for t in annotation.tokens]
#             ta_text_list = [a["metadata"]["text"] for a in ta]
#             text2 = " ".join(ta_text_list)
#             print(text2)
#             print()
#             if text1 != text2:
#                 ic(text1, text2)
#
#
# def token_id(token: Token) -> str:
#     return f"{token.sentence_num}-{token.token_num}"
#
#
# def web_anno_file_paths(folder: str) -> List[str]:
#     return glob.glob(f"{folder}/*.tsv")
#
#
# def load_word_and_token_annotations(doc_id):
#     with open(f"out/{doc_id}-metadata.json") as jf:
#         metadata = json.load(jf)
#     # ic(metadata)
#     word_annotations = [a for a in metadata["annotations"] if a["type"] == "tt:Word"]
#     token_annotations = [a for a in metadata["annotations"] if a["type"] == "tt:Token"]
#     # ic(word_annotations)
#     return word_annotations, token_annotations
#
#
# def make_doc_id(p):
#     return p.split('/')[-1].replace('.tsv', '')
#

@logger.catch
def get_arguments():
    parser = argparse.ArgumentParser(
        description="Show a webannno-tsv file in a more readable format",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("file",
                        help="The webanno-tsv file",
                        type=str)
    return parser.parse_args()


@logger.catch
def display_webanno_tsv(file: str):
    with open(file) as f:
        lines = f.readlines()
    in_table = False
    table = init_table()
    layer_feature_count = [3]
    rows = []
    for line in lines:
        line = line.strip()
        if "\t" not in line:
            if in_table:
                print_table(rows, table, layer_feature_count)
                in_table = False
                rows = []
                table = init_table()
            if is_format_line(line):
                print(yellow(line))
            elif is_layer_definition(line):
                print(green(line))
                layer_feature_count.append(line.count("|"))
            else:
                print(blue(line))
        else:
            if not in_table:
                in_table = True
            rows.append(line.split("\t"))
    if in_table:
        print_table(rows, table, layer_feature_count)


def print_table(rows, table, layer_feature_count):
    column_format = init_column_format(layer_feature_count)
    row_size = len(rows[0])
    header_row = ["id", "char-range", "token"] + ([""] * (row_size - 3))
    rows.insert(0, header_row)
    table.add_rows(rows)
    table.column_format = column_format
    print(table.draw())


def init_column_format(layer_feature_count):
    colors = ['bright_white', 'bright_green', 'bright_blue', 'bright_cyan', 'bright_yellow', 'bright_magenta']
    start = 0
    column_format = []
    for l, lfc in enumerate(layer_feature_count):
        for i in range(start, start + lfc):
            column_format.append(colors[l])
        start += lfc
    return column_format


def init_table():
    table = Blessedtable(max_width=0)
    return table


def is_format_line(line: str) -> bool:
    return line.startswith("#FORMAT=")


def is_layer_definition(line: str) -> bool:
    return line.startswith("#T_")


def blue(text: str):
    return colorize(text, Fore.LIGHTBLUE_EX)


def yellow(text: str):
    return colorize(text, Fore.YELLOW)


def green(text: str):
    return colorize(text, Fore.LIGHTGREEN_EX)


def colorize(text: str, text_color: str):
    return f"{text_color}{text}{Fore.RESET}"


if __name__ == '__main__':
    args = get_arguments()
    if args.file:
        display_webanno_tsv(args.file)
