#!/usr/bin/env python3
import argparse
import os.path
from datetime import datetime
from typing import Optional
from xml.dom.minidom import parseString, Document

import lxml
import pagexml.parser as px
from loguru import logger
from lxml import etree

import globalise_tools.document_metadata as DM
import globalise_tools.git_tools as git
from globalise_tools.document_metadata import DocumentMetadata

fixable_error_codes = ['3.1.1', '3.1.2', '3.2']


@logger.catch
def get_arguments():
    parser = argparse.ArgumentParser(
        description="Read the given PageXML files and fix the reading order when required."
                    " When the reading order is fixed, write the PageXML with the modified reading order"
                    " to the given export directory",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i",
                        "--input-directory",
                        required=True,
                        help="The directory where the original PageXML files are stored, grouped by inventory number.",
                        type=str)
    parser.add_argument("-o",
                        "--output-directory",
                        required=True,
                        help="The directory to store the modified PageXML files in.",
                        type=str)
    parser.add_argument("-m",
                        "--document-metadata-path",
                        required=True,
                        help="The path to the document_metadata.csv file containing the document definitions.",
                        type=str)
    # parser.add_argument("pagexml_path",
    #                     help="The path to the pagexml file",
    #                     nargs="*",
    #                     type=str)
    return parser.parse_args()


class PageXmlFixer:
    def __init__(self, import_path: str, output_directory: str, quality_check: str):
        self.import_path = import_path
        self.output_directory = output_directory
        self.quality_check = quality_check
        self.scan_doc = px.parse_pagexml_file(self.import_path)
        self.pagexml_has_changed = False

    def fix(self):
        filename = self.import_path.split("/")[-1]
        export_path = f"{self.output_directory}/{filename}"
        current_reading_order = self.scan_doc.reading_order
        new_reading_order = self._order_paragraphs_by_y()
        self.pagexml_has_changed = current_reading_order != new_reading_order
        relevant_error_codes = self._extract_relevant_error_codes()
        self._modify_page_xml(export_path, new_reading_order, relevant_error_codes)

    def _order_paragraphs_by_y(self):
        current_reading_order = self.scan_doc.reading_order
        paragraphs = [tr for tr in self.scan_doc.get_text_regions_in_reading_order() if
                      'paragraph' in self._defining_types(tr)]
        replacements = {}
        if self._is_portrait():
            local_replacements = self._ref_id_replacement_dict(paragraphs)
            replacements.update(local_replacements)
        else:
            middle_x = self.scan_doc.coords.box['w'] / 2
            left_paragraphs = [tr for tr in paragraphs if tr.coords.box['x'] < middle_x]
            right_paragraphs = [tr for tr in paragraphs if tr.coords.box['x'] >= middle_x]
            if len(left_paragraphs) > 1:
                local_replacements = self._ref_id_replacement_dict(left_paragraphs)
                replacements.update(local_replacements)
            if len(right_paragraphs) > 1:
                local_replacements = self._ref_id_replacement_dict(right_paragraphs)
                replacements.update(local_replacements)
        new_reading_order = {}
        for i, ref_id in current_reading_order.items():
            if ref_id in replacements.keys():
                new_reading_order[i] = replacements[ref_id]
            else:
                new_reading_order[i] = ref_id
        return new_reading_order

    @staticmethod
    def _defining_types(tr):
        return sorted(tr.types - {'pagexml_doc', 'physical_structure_doc', 'structure_doc', 'text_region'})

    def _is_portrait(self) -> bool:
        box = self.scan_doc.coords.box
        w = box['w']
        h = box['h']
        return (w / h) < 0.9

    @staticmethod
    def _ref_id_replacement_dict(paragraphs):
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

    def _extract_relevant_error_codes(self) -> str:
        error_codes = []
        for fec in fixable_error_codes:
            if fec in self.quality_check:
                error_codes.append(fec)
        return " + ".join(error_codes)

    def _modify_page_xml(self, out_path: str, new_reading_order: dict[int, str], error_codes: str):
        tree = etree.parse(self.import_path)
        root = tree.getroot()
        page = self._get_page_element(root)
        self._set_new_reading_order(page, new_reading_order)
        metadata = self._get_metadata_element(root)
        self._update_last_change(metadata)
        self._add_processing_step(metadata, error_codes)
        self._reorder_text_regions(page, new_reading_order)
        if self.pagexml_has_changed:
            self._write_to_xml(tree, out_path)

    def _get_page_element(self, root):
        page_index = self._element_index(root, 'Page')
        page = root[page_index]
        return page

    def _add_processing_step(self, metadata, error_codes: str):
        commit_id = git.read_current_commit_id()
        metadata_item = etree.Element(
            "MetadataItem",
            attrib={
                "type": "processingStep",
                "name": "fix-reading-order",
                "value": "globalise-tools/scripts/gt-fix-reading-order.py"
            }
        )
        labels = etree.SubElement(metadata_item, "Labels")
        labels.append(self._label_element("githash", commit_id))
        script_permalink = f"https://github.com/knaw-huc/globalise-tools/blob/{commit_id}/scripts/gt-fix-reading-order.py"
        labels.append(self._label_element("url", script_permalink))
        labels.append(self._label_element("fixed_error_codes", error_codes))
        metadata[-1].addprevious(metadata_item)

    @staticmethod
    def _label_element(label_type: str, label_value: str) -> etree.Element:
        return etree.Element("Label", attrib={"type": label_type, "value": label_value})

    @staticmethod
    def _write_to_xml(doc: Document, path: str):
        xml_str = etree.tostring(doc, pretty_print=True, xml_declaration=True, encoding="UTF-8")
        pretty_xml_lines = parseString(xml_str).toprettyxml(indent="  ").split('\n')
        clean_xml = "\n".join([l for l in pretty_xml_lines if l.strip()])
        logger.info(f"=> {path}")
        with open(path, 'w') as xml_file:
            xml_file.write(
                clean_xml.replace('<?xml version="1.0" ?>', '<?xml version="1.0" encoding="UTF-8"?>').replace('\n"',
                                                                                                              '"')
            )

    @staticmethod
    def _element_index(element: lxml.etree._Element, sub_element_name: str) -> Optional[int]:
        for i, sub_element in enumerate(list(element)):
            tag_prefix = '{' + sub_element.nsmap[sub_element.prefix] + '}'
            expected_tag = tag_prefix + sub_element_name
            if sub_element.tag == expected_tag:
                return i
        return None

    def _set_new_reading_order(self, page, new_reading_order):
        reading_order_index = self._element_index(page, 'ReadingOrder')
        reading_order = page[reading_order_index]
        ordered_group = reading_order[0]
        for index, region_ref in new_reading_order.items():
            ordered_group[index] = etree.Element("RegionRefIndexed", {"index": str(index), "regionRef": region_ref})

    def _get_metadata_element(self, root):
        metadata_index = self._element_index(root, 'Metadata')
        metadata = root[metadata_index]
        return metadata

    def _update_last_change(self, metadata):
        last_changed_element_index = self._element_index(metadata, 'LastChange')
        if last_changed_element_index:
            metadata[last_changed_element_index].text = datetime.today().strftime('%Y-%m-%dT%H:%M:%S')
        else:
            logger.warning(f"no LastChange element found in Metadata")

    def _reorder_text_regions(self, page_element: lxml.etree._Element, new_reading_order: dict[int, str]):
        reading_orders = []
        text_region_dict = {}
        for child in page_element:
            if 'TextRegion' in child.tag:
                tr_id = child.attrib['id']
                text_region_dict[tr_id] = child
            elif 'ReadingOrder' in child.tag:
                reading_orders.append(child)
            else:
                logger.error(f"unexpected Page child: {child.tag}")
            page_element.remove(child)
        for ro in reading_orders:
            page_element.append(ro)
        ro_keys_in_order = sorted(new_reading_order.keys())
        for ro_key in ro_keys_in_order:
            text_region = text_region_dict[new_reading_order[ro_key]]
            self._reorder_lines(text_region)
            page_element.append(text_region)

    def _reorder_lines(self, text_region_element: lxml.etree._Element):
        coords = []
        text_line_element_dict = {}
        text_region_id = text_region_element.attrib['id']
        text_region = [tr for tr in self.scan_doc.text_regions if tr.id == text_region_id][0]
        text_lines = text_region.lines
        sorted_text_lines = sorted(text_lines, key=lambda l: l.coords.box['y'])
        if text_lines == sorted_text_lines:
            return

        self.pagexml_has_changed = True
        sorted_text_line_ids = [l.id for l in sorted_text_lines]
        for child in text_region_element:
            if 'TextLine' in child.tag:
                tl_id = child.attrib['id']
                text_line_element_dict[tl_id] = child
            elif 'Coords' in child.tag:
                coords.append(child)
            else:
                logger.error(f"unexpected TextRegion child: {child.tag}")
            text_region_element.remove(child)
        for c in coords:
            text_region_element.append(c)
        for line_id in sorted_text_line_ids:
            text_region_element.append(text_line_element_dict[line_id])


@logger.catch
def fix_reading_order(input_directory: str, output_directory: str, document_metadata_path: str):
    logger.info(f"<= {document_metadata_path}")
    relevant_documents = [r for r in DM.read_document_metadata(document_metadata_path) if is_relevant(r)]
    pagexml_paths = []
    quality_check = {}
    for dm in relevant_documents:
        pagexml_dir = f"{input_directory}/{dm.inventory_number}"
        for pid in dm.pagexml_ids:
            pagexml_path = f"{pagexml_dir}/{pid}.xml"
            pagexml_paths.append(pagexml_path)
            quality_check[pagexml_path] = dm.quality_check
    total = len(pagexml_paths)
    for i, import_path in enumerate(pagexml_paths):
        logger.info(f"<= {import_path} ({i + 1}/{total})")
        if os.path.exists(import_path):
            PageXmlFixer(import_path, output_directory, quality_check[import_path]).fix()
        else:
            logger.warning(f"missing file: {import_path}")


def is_relevant(document_metadata: DocumentMetadata) -> bool:
    quality_check = document_metadata.quality_check
    return '3.1.1' in quality_check or '3.1.2' in quality_check or '3.2' in quality_check and document_metadata.scan_range != ""


# def has_problematic_text_region_reading_order(pd: pdm.PageXMLDoc) -> bool:
#     paragraphs = [tr for tr in pd.get_text_regions_in_reading_order() if 'paragraph' in defining_types(tr)]
#     if len(paragraphs) > 1:
#         if is_portrait(pd):
#             y_values = [p.coords.box['y'] for p in paragraphs]
#             sorted_y_values = sorted(y_values)
#             is_problematic = y_values != sorted_y_values
#             if is_problematic:
#                 # print("problematic paragraph reading order because of y_value order")
#                 return is_problematic
#         else:
#             # assume 2 pages
#             middle_x = pd.coords.box['w'] / 2
#             left_paragraphs = [tr for tr in paragraphs if tr.coords.box['x'] < middle_x]
#             right_paragraphs = [tr for tr in paragraphs if tr.coords.box['x'] >= middle_x]
#             if len(left_paragraphs) > 1:
#                 y_values = [p.coords.box['y'] for p in left_paragraphs]
#                 sorted_y_values = sorted(y_values)
#                 if y_values != sorted_y_values:
#                     # print("problematic paragraph reading order because of y_value order in left page")
#                     return True
#             if len(right_paragraphs) > 1:
#                 y_values = [p.coords.box['y'] for p in right_paragraphs]
#                 sorted_y_values = sorted(y_values)
#                 if y_values != sorted_y_values:
#                     # print("problematic paragraph reading order because of y_value order in right page")
#                     return True
#             return False
#     else:
#         return False


if __name__ == '__main__':
    args = get_arguments()
    if args.document_metadata_path:
        fix_reading_order(args.input_directory, args.output_directory, args.document_metadata_path)
