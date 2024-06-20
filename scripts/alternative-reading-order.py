import csv
from dataclasses import dataclass, field
from xml.dom.minidom import parseString, Document

import pagexml.parser as px
from IPython.display import display, HTML
from dataclasses_json import dataclass_json
from loguru import logger
from lxml import etree

base_pagexml_path = "/Users/bram/workspaces/globalise/pagexml"


# lees data/document_metadata.json
# select documents with 3.1.1, 3.1.2 or 3.2 in quality check
# for the pages in the indicated range: adjust the reading order, and write the modified pagexml
@dataclass
class XYWH:
    x: int
    y: int
    w: int
    h: int


def scan_map():
    path = "/Users/bram/workspaces/globalise/globalise-tools/data/iiif-url-mapping.csv"
    iiif_base_url_idx = {}
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            iiif_base_url_idx[row["pagexml_id"]] = row["iiif_base_url"]
    return iiif_base_url_idx


iiif_base_url_idx = scan_map()


def bounding_box(c) -> str:
    box = c.box
    return f"{box['x']:4},{box['y']:4},{box['w']:4},{box['h']:4}"


def extend_box(box, extra_points: int):
    x1 = max(0, box['x'] - extra_points)
    y1 = max(0, box['y'] - extra_points)
    w1 = box['w'] + 2 * extra_points
    h1 = box['h'] + 2 * extra_points
    return f"{x1},{y1},{w1},{h1}"


def show(inv_nr: str, page_no: str):
    scan_doc = px.parse_pagexml_file(pagexml_file=page_xml_path(inv_nr, page_no))
    key = page_xml_id(inv_nr, page_no)
    base_iiif_url = iiif_base_url_idx[key]
    print(scan_doc.metadata['scan_id'])
    print(f"{base_iiif_url}/full/full/0/default.jpg")
    for i, tr in enumerate(scan_doc.get_text_regions_in_reading_order()):
        if tr.lines:
            text = " ".join([l.text for l in tr.lines])
        else:
            text = ""
        bb = bounding_box(tr.coords)
        print(i, bb, defining_types(tr), '"' + text + '"')
        extended_xywh = extend_box(tr.coords.box, 75)
        img = f"""<img src="{base_iiif_url}/{extended_xywh}/full/0/default.jpg"/>"""
        display(HTML(img))


def page_xml_path(inv_nr: str, page_no: str) -> str:
    return f"{base_pagexml_path}/{inv_nr}/NL-HaNA_1.04.02_{inv_nr}_{page_no}.xml"


def page_xml_id(inv_nr, page_no):
    return f"NL-HaNA_1.04.02_{inv_nr}_{page_no}"


def show_boxes(base: str, width: int, height: int, boxes: list[XYWH]):
    style = """
    <style>
        .container {
            position: relative;
            display: inline-block;
        }
        .overlay {
            position: absolute;
            top: 0;
            left: 0;
        }
    </style>
    """
    svg_content = []
    for i, box in enumerate(boxes):
        points = []
        x0 = int(box.x / 2)
        x1 = int((box.x + box.w) / 2)
        y0 = int(box.y / 2)
        y1 = int((box.y + box.h) / 2)
        points.append(f"{x0},{y0}")
        points.append(f"{x1},{y0}")
        points.append(f"{x1},{y1}")
        points.append(f"{x0},{y1}")
        polygon = f"""<polygon points="{" ".join(points)}" fill="rgba(0, 0, 255, 0.1)" stroke="blue" stroke-width="2"/>"""
        svg_content.append(polygon)

        mid_x = int((box.x + (box.w / 2)) / 2)
        mid_y = int((box.y + (box.h / 2)) / 2)
        text = f"""<text x="{mid_x}" y="{mid_y}" font-size="40" text-anchor="middle" fill="white">{i + 1}</text>"""
        svg_content.append(text)
    svg = '\n'.join(svg_content)
    div = f"""
    {style}
    <div class="container">
        <img src="{base}/full/full/0/default.jpg" alt="Image" width="{width}" height="{height}">
        <svg class="overlay" width="{width}" height="{height}">
        {svg}
        </svg>
    </div>
    """
    # print(div)
    display(HTML(div))


def update_page_xml():
    show(inv_nr="1431", page_no="0910")

    path = page_xml_path("3211", "0042")







