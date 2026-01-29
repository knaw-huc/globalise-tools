import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Iterator

import globalise_tools.git_tools as git
import globalise_tools.url_factory as uf
from globalise_tools.creator import CreatorFactory
from globalise_tools.model import Offset

ns = {
    'ns': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'
}


class AnnotationPageBuilder:

    def __init__(
            self,
            xml_string: str,
            page_id: str = "",
            canvas_id: str = "",
            page_text: str = "",
            script_path: str = "",
            commit_id: Optional[str] = None
    ) -> None:
        self.page_id = page_id
        self.xml_string = xml_string
        self.canvas_id = canvas_id
        self.page_text = page_text
        self.script_path = script_path
        if not commit_id:
            self.commit_id = git.read_current_commit_id(warn_on_uncommitted_changes=True)
        else:
            self.commit_id = commit_id

    # ---------------- Main converter ----------------
    def build(self) -> Dict[str, Any]:
        annotations = []

        doc = ET.fromstring(self.xml_string)

        # Root elements
        page = self._find_first(doc, "Page")
        page_filename = self._get_attr(page, "imageFilename")
        width = int(self._get_attr(page, "imageWidth") or 0) or None
        height = int(self._get_attr(page, "imageHeight") or 0) or None

        base = re.sub(r"\.[a-zA-Z]+$", "", page_filename or "page")
        ap_uri = uf.annotation_page_url(uf.AnnotationPageType.TRANSCRIPTIONS, base)
        # base_id = (f"{URI_BASE_PATTERN}annotations:transcriptions:{urllib.parse.quote(base)}")

        block_idx = line_idx = word_idx = 0
        page_anno_id = f"{ap_uri}#page-normalized"
        text_lines: List[str] = []

        # Regions
        for region in self._find_all(page, "TextRegion"):
            block_idx += 1
            region_coords = self._find_first(region, "Coords")
            region_points = self._get_attr(region_coords, "points")
            region_svg = self._points_to_svg_path(region_points)
            region_id_raw = self._get_attr(region, "id") or f"block{block_idx}"
            block_anno_id = f"{ap_uri}#{region_id_raw}"

            if region_svg:
                annotations.append(
                    self._build_annotation(
                        id=block_anno_id,
                        granularity="block",
                        svg_path=region_svg,
                        body_classification=self._get_region_type(region),
                        annotation_targets=[page_anno_id],
                    )
                )

            # Lines
            for line in self._find_all(region, "TextLine"):
                line_idx += 1
                line_coords = self._find_first(line, "Coords")
                line_points = self._get_attr(line_coords, "points")
                line_svg = self._points_to_svg_path(line_points)
                line_text = self._extract_text(line)
                line_id_raw = self._get_attr(line, "id") or f"line{line_idx}"
                line_anno_id = f"{ap_uri}#{line_id_raw}"

                if line_text:
                    text_lines.append(line_text)

                if line_svg or line_text:
                    annotations.append(
                        self._build_annotation(
                            id=line_anno_id,
                            granularity="line",
                            svg_path=line_svg,
                            annotation_targets=[block_anno_id],
                            body_text=line_text,
                        )
                    )

                # Words
                for w in self._find_all(line, "Word"):
                    word_idx += 1
                    w_coords = self._find_first(w, "Coords")
                    w_points = self._get_attr(w_coords, "points")
                    word_svg = self._points_to_svg_path(w_points)
                    w_text = self._extract_text(w)
                    word_id_raw = self._get_attr(w, "id") or f"word{word_idx}"
                    word_anno_id = f"{ap_uri}#{word_id_raw}"

                    if word_svg or w_text:
                        annotations.append(
                            self._build_annotation(
                                id=word_anno_id,
                                granularity="word",
                                svg_path=word_svg,
                                annotation_targets=[line_anno_id],
                                body_text=w_text,
                                text_position=Offset(begin=0, end=0)
                            )
                        )

        # Page
        annotations.append(
            self._build_annotation(
                id=page_anno_id,
                granularity="page",
                body_text=self.page_text,
            )
        )
        annotations.append(
            self._build_annotation(
                id=page_anno_id.replace("normalized", "htr"),
                granularity="page-htr",
                body_text="\n".join(text_lines),
            )
        )

        cf = CreatorFactory(script_paths=[self.script_path], commit_id=self.commit_id)
        creator = cf.creator(
            label="Creation of Web Annotations from PageXML HTR output (generated by the GLOBALISE Loghi HTR model).")

        annotation_page = {
            "@context": [
                "http://iiif.io/api/extension/text-granularity/context.json",
                "http://iiif.io/api/presentation/3/context.json",
                "https://linked.art/ns/v1/linked-art.json",
                "https://objectstore.surf.nl/87435b768620494e8e911c83d1997f24:globalise-data/contexts/crmdig.json",
                "http://www.w3.org/ns/anno.jsonld",
                {
                    "transcription-diplomatic": {
                        "@id": "https://digitaalerfgoed.poolparty.biz/globalise/annotation/transcription/transcription-diplomatic"
                    },
                    "transcription-normalized": {
                        "@id": "https://digitaalerfgoed.poolparty.biz/globalise/annotation/transcription/transcription-normalized"
                    }
                }
            ],
            "type": ["DigitalObject", "AnnotationPage"],
            "id": ap_uri,
            "label": f"Transcription of {page_filename}",
            "created_by": creator,
            "items": annotations,
        }

        if self.canvas_id and width and height:
            annotation_page["partOf"] = {
                "id": self.canvas_id,
                "type": "Canvas",
                "height": height,
                "width": width,
            }

        return annotation_page

    def get_word_offsets(self) -> Dict[str, Offset]:
        doc = ET.fromstring(self.xml_string)

        # Root elements
        page = self._find_first(doc, "Page")
        word_idx = 0
        htr_word_offset = {}
        offset = 0

        for region in self._find_all(page, "TextRegion"):
            for line in self._find_all(region, "TextLine"):
                for w in self._find_all(line, "Word"):
                    word_idx += 1
                    w_text = self._extract_text(w)
                    w_len = len(w_text)
                    word_id_raw = self._get_attr(w, "id") or f"word{word_idx}"
                    htr_word_offset[word_id_raw] = Offset(offset, offset + w_len)
                    offset += w_len + 1

        return htr_word_offset

    # ---------------- Annotation builder ----------------

    def _build_annotation(
            self,
            id: str,
            granularity: Optional[str] = None,
            svg_path: Optional[str] = None,
            annotation_targets: Optional[List[str]] = None,
            body_text: Optional[str] = None,
            body_classification: Optional[str] = None,
            text_position: Optional[Offset] = None,
    ) -> Dict[str, Any]:
        body = []
        if body_text:
            body.append({"type": "TextualBody", "value": body_text})
        if body_classification:
            # classification_uri = (
            #         f"{uf.URI_BASE_PATTERN}thesaurus:annotation:"
            #         + urllib.parse.quote(body_classification)
            # )
            classification_uri = uf.concept_url(f"annotation:{body_classification}")
            body.append({
                "type": "SpecificResource",
                "source": {
                    "id": classification_uri,
                    "type": "skos:Concept",
                    "label": body_classification,
                },
                "purpose": "classifying",
            })

        target = []
        if self.canvas_id and svg_path:
            target.append({
                "type": "SpecificResource",
                "source": self.canvas_id,
                "selector": {"type": "SvgSelector", "value": svg_path},
            })

        for t in annotation_targets or []:
            target.append({"id": t, "type": "Annotation"})

        if text_position:
            target.append(self.text_position_target(text_position))

        anno = {
            "type": "Annotation",
            "id": id,
            "motivation": "supplementing" if body_text else "highlighting",
            "textGranularity": granularity,
        }
        if granularity == "page":
            anno["purpose"] = "transcription-normalized"
            target.append({"type": "Canvas", "id": self.canvas_id})
        if granularity == "page-htr":
            anno["textGranularity"] = "page"
            anno["purpose"] = "transcription-diplomatic"
            target.append({"type": "Canvas", "id": self.canvas_id})
        if body:
            anno["body"] = body
        if target:
            anno["target"] = target
        return anno

    def text_position_target(self, text_position: Offset) -> dict[str, Any]:
        return {
            "type": "SpecificResource",
            "source": {
                "id": f"{uf.annotation_page_url(uf.AnnotationPageType.TRANSCRIPTIONS, self.page_id)}#page-htr",
                "type": [
                    "DigitalObject",
                    "Annotation"
                ]
            },
            "selector": [
                {
                    "type": "TextPositionSelector",
                    "start": text_position.begin,
                    "end": text_position.end
                }
            ]
        }

    # ---------------- XML helpers ----------------

    @staticmethod
    def _is_element(node: Optional[ET.Element]) -> bool:
        return node is not None and isinstance(node.tag, str)

    def _child_elements(self, node: Optional[ET.Element]) -> Iterator[ET.Element]:
        if node is None:
            return (c for c in [])
        return (c for c in node if self._is_element(c))

    def _find_first(self, node: Optional[ET.Element], name: str) -> Optional[ET.Element]:
        for c in self._child_elements(node):
            if c.tag == f"{{{ns['ns']}}}{name}":
                return c
        return None

    def _find_all(self, node: Optional[ET.Element], name: str) -> List[ET.Element]:
        return [c for c in self._child_elements(node) if c.tag == f"{{{ns['ns']}}}{name}"]

    @staticmethod
    def _get_attr(node: Optional[ET.Element], key: str) -> Optional[str]:
        if node is None:
            return None
        return node.attrib.get(key)

    @staticmethod
    def _points_to_svg_path(points: Optional[str]) -> Optional[str]:
        if not points:
            return None
        trimmed = re.sub(r"\s+", " ", points.strip())
        return f'<path d="M{trimmed}z"/>'

    def _get_region_type(self, region: Optional[ET.Element]) -> Optional[str]:
        """Extracts the 'type' from a custom attribute like: structure {type:page-number;}"""
        if region is None:
            return None
        custom = self._get_attr(region, "custom")
        if not custom:
            return None
        m = re.search(r"structure\s*\{([^}]*)}", custom, re.I)
        inside = m.group(1) if m else custom
        t = re.search(r"\btype\s*:\s*([^;\s}]+)", inside, re.I)
        return t.group(1).strip() if t else None

    def _extract_text(self, node: Optional[ET.Element]) -> Optional[str]:
        if node is None:
            return None
        text_equiv = self._find_first(node, "TextEquiv")
        unicode_el = self._find_first(text_equiv, "Unicode")
        if unicode_el is not None and len(unicode_el) == 0 and unicode_el.text:
            return unicode_el.text.strip() or None
        if unicode_el is not None and unicode_el.text:
            return unicode_el.text.strip() or None
        return None
