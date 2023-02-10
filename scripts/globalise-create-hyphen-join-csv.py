#!/usr/bin/env python3
import csv
from itertools import chain

import tabulate
import xlsxwriter
from loguru import logger
from pagexml.parser import parse_pagexml_file

from globalise_tools.tools import na_url

data_dir = '/Users/bram/workspaces/globalise/globalise-tools/data'
headers = ["scan", "n", "line n", "join?", "new paragraph?", "line n+1", "below/next", "roi n", "roi n+1"]

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


def as_file_lines(filename):
    path = f"{data_dir}/{filename}"
    scan_doc = parse_pagexml_file(path)
    lines = scan_doc.get_lines()
    return [(filename, line) for line in lines]


def as_rows(filename):
    url = na_url(filename)
    path = f"{data_dir}/{filename}"
    scan_doc = parse_pagexml_file(path)
    lines = scan_doc.get_lines()
    rows = []
    for i, line in enumerate(lines[:-1]):
        if i < len(lines) - 1:
            next_line = lines[i + 1]
            bn = ""
            if next_line.is_below(line):
                bn += "b"
            if line.is_next_to(next_line):
                bn += "n"
            roi_n = line.metadata['reading_order']['index']
            roi_n1 = next_line.metadata['reading_order']['index']
            row = [url, i, line.text, "", next_line.text, bn, roi_n, roi_n1]
            rows.append(row)
    return rows


def to_rows(file_lines):
    rows = []
    for i, file_line in enumerate(file_lines[:-1]):
        url = na_url(file_line[0])
        line = file_line[1]
        next_line = file_lines[i + 1][1]
        bn = ""
        if next_line.is_below(line):
            bn += "b"
        if line.is_next_to(next_line):
            bn += "n"
        roi_n = int(line.metadata['reading_order']['index'])
        roi_n1 = int(next_line.metadata['reading_order']['index'])
        par_break = (bn == "") or (roi_n1 <= roi_n)
        row = [url, i, line.text, False, par_break, next_line.text, bn, roi_n, roi_n1]
        rows.append(row)
    return rows


def write_to_csv(csv_path, data):
    with open(csv_path, "w", encoding="utf-8") as f:
        writer = csv.writer(f, dialect='excel', delimiter=",")
        writer.writerow(headers)
        writer.writerows(data)


def write_to_xlsx(xlsx, data):
    workbook = xlsxwriter.Workbook(xlsx)
    header_format = workbook.add_format(
        {'bold': True, 'bg_color': 'cyan', 'align': 'center', 'locked': True, 'border': 6})
    unlocked_center_format = workbook.add_format({'align': 'center', 'locked': False})
    locked_right_format = workbook.add_format({'align': 'right', 'locked': True})
    locked_center_format = workbook.add_format({'align': 'center', 'locked': True})
    locked_format = workbook.add_format({'locked': True})
    worksheet = workbook.add_worksheet()
    worksheet.protect()
    worksheet.set_column('A:A', 25)
    worksheet.set_column('B:B', 4, None, {"collapsed": 1})
    worksheet.set_column('C:C', 60)
    worksheet.set_column('D:D', 6)
    worksheet.set_column('E:E', 15)
    worksheet.set_column('F:F', 60)
    worksheet.set_column('G:G', 10, locked_center_format)
    worksheet.set_column('H:I', 6, locked_center_format)
    worksheet.write_row(row=0, col=0, data=headers, cell_format=header_format)
    for i, data_row in enumerate(data):
        row = i + 1
        url = data_row[0]
        worksheet.write_url(row, 0, url, cell_format=locked_format, string=url.split('/')[-1])
        worksheet.write(row, 1, data_row[1], locked_format)
        worksheet.write(row, 2, data_row[2], locked_right_format)
        worksheet.write(row, 3, "X" if data_row[3] else "", unlocked_center_format)
        worksheet.write(row, 4, "X" if data_row[4] else "", unlocked_center_format)
        worksheet.write(row, 5, data_row[5], locked_format)
        worksheet.write(row, 6, data_row[6], locked_format)
        worksheet.write_number(row, 7, int(data_row[7]))
        worksheet.write_number(row, 8, int(data_row[8]))
    workbook.close()


@logger.catch
def main():
    lines_per_file = [as_file_lines(file) for file in files]
    file_lines = list(chain(*lines_per_file))
    data = to_rows(file_lines)

    table = tabulate.tabulate(
        data,
        tablefmt='github',
        headers=headers,
        colalign=["left", "right", "right", "left", "center", "center", "center", "center"]
    )
    # print(table)

    write_to_csv('out.csv', data)
    write_to_xlsx('globalise-word-joins.xlsx', data)


if __name__ == '__main__':
    main()
