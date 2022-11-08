#!/usr/bin/env python3
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Print text range defined by offset and length from given text file",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("file",
                        help="The file to print the range from.",
                        type=str)
    parser.add_argument("-o", "--offset",
                        required=True,
                        help="The start of the range to print, in unicode codepoints",
                        type=int)
    parser.add_argument("-l", "--length",
                        required=True,
                        help="The length of the range to print, in unicode codepoints",
                        type=int)
    args = parser.parse_args()

    if args.file:
        trange = text_range(args.file, args.offset, args.length)
        print(trange)


def text_range(file, offset, length):
    with open(file, 'r', encoding='utf-8') as f:
        text = f.read()
    end = offset + length
    return text[offset:end]


if __name__ == '__main__':
    main()
