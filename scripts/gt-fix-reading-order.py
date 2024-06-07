#!/usr/bin/env python3
import argparse
from datetime import datetime
from typing import Optional
from xml.dom.minidom import parseString, Document

import lxml
import pagexml.model.physical_document_model as pdm
import pagexml.parser as px
from loguru import logger
from lxml import etree


@logger.catch
def get_arguments():
    parser = argparse.ArgumentParser(
        description="Read the given PageXML files and fix the reading order when required."
                    " When the reading order is fixed, write the PageXML with the modified reading order"
                    " to the given export directory",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-o",
                        "--output-directory",
                        required=True,
                        help="The directory to store the modified PageXML files in.",
                        type=str)
    parser.add_argument("pagexml_path",
                        help="The path to the pagexml file",
                        nargs="*",
                        type=str)
    return parser.parse_args()


@logger.catch
def fix_reading_order(pagexml_paths: list[str], output_directory: str):
    for import_path in pagexml_paths:
        scan_doc = px.parse_pagexml_file(import_path)
        if has_problematic_reading_order(scan_doc):
            filename = import_path.split("/")[-1]
            export_path = f"{output_directory}/{filename}"
            new_reading_order = order_paragraphs_by_y(scan_doc)
            modify_page_xml(import_path, export_path, new_reading_order)


def order_paragraphs_by_y(scan_doc: pdm.PageXMLDoc):
    current_reading_order = scan_doc.reading_order
    paragraphs = [tr for tr in scan_doc.get_text_regions_in_reading_order() if 'paragraph' in defining_types(tr)]
    replacements = {}
    if is_portrait(scan_doc):
        local_replacements = ref_id_replacement_dict(paragraphs)
        replacements.update(local_replacements)
    else:
        middle_x = scan_doc.coords.box['w'] / 2
        left_paragraphs = [tr for tr in paragraphs if tr.coords.box['x'] < middle_x]
        right_paragraphs = [tr for tr in paragraphs if tr.coords.box['x'] >= middle_x]
        if len(left_paragraphs) > 1:
            local_replacements = ref_id_replacement_dict(left_paragraphs)
            replacements.update(local_replacements)
        if len(right_paragraphs) > 1:
            local_replacements = ref_id_replacement_dict(right_paragraphs)
            replacements.update(local_replacements)
    new_reading_order = {}
    for i, ref_id in current_reading_order.items():
        if ref_id in replacements.keys():
            new_reading_order[i] = replacements[ref_id]
        else:
            new_reading_order[i] = ref_id
    return new_reading_order


def ref_id_replacement_dict(paragraphs):
    par_y_list = [(tr.id, tr.coords.box['y']) for tr in paragraphs]
    sorted_par_y_list = sorted(par_y_list, key=lambda t: t[1])
    zipped = zip(par_y_list, sorted_par_y_list)
    local_replacements = {}
    for z in zipped:
        original_id = z[0][0]
        new_id = z[1][0]
        if original_id != new_id:
            local_replacements[original_id] = new_id
    return local_replacements


def has_problematic_reading_order(pd: pdm.PageXMLDoc) -> bool:
    paragraphs = [tr for tr in pd.get_text_regions_in_reading_order() if 'paragraph' in defining_types(tr)]
    if len(paragraphs) > 1:
        if is_portrait(pd):
            y_values = [p.coords.box['y'] for p in paragraphs]
            sorted_y_values = sorted(y_values)
            is_problematic = y_values != sorted_y_values
            if is_problematic:
                # print("problematic paragraph reading order because of y_value order")
                return is_problematic
        else:
            # assume 2 pages
            middle_x = pd.coords.box['w'] / 2
            left_paragraphs = [tr for tr in paragraphs if tr.coords.box['x'] < middle_x]
            right_paragraphs = [tr for tr in paragraphs if tr.coords.box['x'] >= middle_x]
            if len(left_paragraphs) > 1:
                y_values = [p.coords.box['y'] for p in left_paragraphs]
                sorted_y_values = sorted(y_values)
                if y_values != sorted_y_values:
                    # print("problematic paragraph reading order because of y_value order in left page")
                    return True
            if len(right_paragraphs) > 1:
                y_values = [p.coords.box['y'] for p in right_paragraphs]
                sorted_y_values = sorted(y_values)
                if y_values != sorted_y_values:
                    # print("problematic paragraph reading order because of y_value order in right page")
                    return True
            return False
    else:
        return False


def is_portrait(doc: pdm.PageXMLDoc) -> bool:
    box = doc.coords.box
    w = box['w']
    h = box['h']
    return (w / h) < 0.9


def defining_types(tr):
    return sorted(tr.types - {'pagexml_doc', 'physical_structure_doc', 'structure_doc', 'text_region'})


def element_index(element: lxml.etree._Element, sub_element_name: str) -> Optional[int]:
    for i, sub_element in enumerate(list(element)):
        tag_prefix = '{' + sub_element.nsmap[sub_element.prefix] + '}'
        expected_tag = tag_prefix + sub_element_name
        if sub_element.tag == expected_tag:
            return i
    return None


def modify_page_xml(in_path: str, out_path: str, new_reading_order: dict[int, str]):
    tree = etree.parse(in_path)
    root = tree.getroot()
    page_index = element_index(root, 'Page')
    page = root[page_index]
    reading_order_index = element_index(page, 'ReadingOrder')
    reading_order = page[reading_order_index]
    ordered_group = reading_order[0]
    for index, region_ref in new_reading_order.items():
        ordered_group[index] = etree.Element("RegionRefIndexed", {"index": str(index), "regionRef": region_ref})
    metadata_index = element_index(root, 'Metadata')
    metadata = root[metadata_index]

    last_changed_element_index = element_index(metadata, 'LastChange')
    if last_changed_element_index:
        metadata[last_changed_element_index].text = datetime.today().strftime('%Y-%m-%dT%H:%M:%S')
    else:
        logger.warning(f"no LastChange element found in Metadata")
    metadata_item = etree.Element(
        "MetadataItem",
        attrib={
            "type": "processingStep",
            "name": "fix-reading-order",
            "value": "Paragraphs ordered by y coordinate of bounding box, per page"
        }
    )
    # labels = etree.SubElement(metadata_item, "Labels")
    # labels.append(label_element("label-1", "value-1"))
    # labels.append(label_element("label-2", "value-2"))
    metadata[-1].addprevious(metadata_item)
    write_to_xml(tree, out_path)


def label_element(label_type: str, label_value: str) -> etree.Element:
    return etree.Element("Label", attrib={"type": label_type, "value": label_value})


def write_to_xml(doc: Document, path: str):
    xml_str = etree.tostring(doc, pretty_print=True, xml_declaration=True, encoding="UTF-8")
    pretty_xml_lines = parseString(xml_str).toprettyxml(indent="  ").split('\n')
    clean_xml = "\n".join([l for l in pretty_xml_lines if l.strip()])
    logger.info(f"=> {path}")
    with open(path, 'w') as xml_file:
        xml_file.write(
            clean_xml.replace('<?xml version="1.0" ?>', '<?xml version="1.0" encoding="UTF-8"?>').replace('\n"', '"')
        )


if __name__ == '__main__':
    args = get_arguments()
    if args.pagexml_path:
        fix_reading_order(args.pagexml_path, args.output_directory)
