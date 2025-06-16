import globalise_tools.git_tools as git
import lxml
import pagexml.parser as px

from datetime import datetime
from loguru import logger
from lxml import etree
from typing import Optional
from xml.dom.minidom import parseString, Document


class PageXmlFixer:
    def __init__(self, import_path: str, output_directory: str, quality_check: str, script: str):
        self.import_path = import_path
        self.output_directory = output_directory
        self.quality_check = quality_check
        self.scan_doc = px.parse_pagexml_file(self.import_path)
        self.error_codes = set()
        self.script = script

    def fix(self):
        filename = self.import_path.split("/")[-1]
        export_path = f"{self.output_directory}/{filename}"
        current_reading_order = self.scan_doc.reading_order
        new_reading_order = self._order_paragraphs_by_y()
        if current_reading_order != new_reading_order:
            if self._is_portrait():
                self.error_codes.add("3.1.1")
            else:
                self.error_codes.add("3.1.2")
        self._modify_page_xml(export_path, new_reading_order)

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

    def _modify_page_xml(self, out_path: str, new_reading_order: dict[int, str]):
        tree = etree.parse(self.import_path)
        root = tree.getroot()
        page = self._get_page_element(root)
        self._set_new_reading_order(page, new_reading_order)
        metadata = self._get_metadata_element(root)
        self._update_last_change(metadata)
        self._reorder_text_regions(page, new_reading_order)
        self._add_processing_step(metadata, " + ".join(sorted(self.error_codes)))
        if self.error_codes:
            self._write_to_xml(tree, out_path)

    def _get_page_element(self, root):
        page_index = self._element_index(root, 'Page')
        page = root[page_index]
        return page

    def _add_processing_step(self, metadata, error_codes: str):
        if git.there_are_uncommitted_changes():
            logger.warning("Uncommitted changes! Do a `git commit` first!")
        commit_id = git.read_current_commit_id()
        metadata_item = etree.Element(
            "MetadataItem",
            attrib={
                "type": "processingStep",
                "name": "fix-reading-order",
                "value": f"globalise-tools/scripts/{self.script}}"
            }
        )
        labels = etree.SubElement(metadata_item, "Labels")
        labels.append(self._label_element("githash", commit_id))
        script_permalink = f"https://github.com/knaw-huc/globalise-tools/blob/{commit_id}/scripts/{self.script}"
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
        self.error_codes.add("3.2")
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
