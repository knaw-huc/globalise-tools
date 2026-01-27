import re
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Generator

import globalise_tools.git_tools as git
import globalise_tools.url_factory as uf
from globalise_tools.creator import CreatorFactory
from globalise_tools.model import Offset

ns = {
    'ns': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'
}


# ---------------- XML helpers ----------------

def is_element(node: Optional[ET.Element]) -> bool:
    return node is not None and isinstance(node.tag, str)


def children_elements(node: Optional[ET.Element]) -> Generator[ET.Element]:
    if node is None:
        return (c for c in [])
    return (c for c in node if is_element(c))


def find_first(node: Optional[ET.Element], name: str) -> Optional[ET.Element]:
    for c in children_elements(node):
        if c.tag == f"{{{ns['ns']}}}{name}":
            return c
    return None


def find_all(node: Optional[ET.Element], name: str) -> List[ET.Element]:
    return [c for c in children_elements(node) if c.tag == f"{{{ns['ns']}}}{name}"]


def get_attr(node: Optional[ET.Element], key: str) -> Optional[str]:
    if node is None:
        return None
    return node.attrib.get(key)


def points_to_svg_path(points: Optional[str]) -> Optional[str]:
    if not points:
        return None
    trimmed = re.sub(r"\s+", " ", points.strip())
    return f'<path d="M{trimmed}z"/>'


def get_region_type(region: Optional[ET.Element]) -> Optional[str]:
    """Extracts the 'type' from a custom attribute like: structure {type:page-number;}"""
    if region is None:
        return None
    custom = get_attr(region, "custom")
    if not custom:
        return None
    m = re.search(r"structure\s*\{([^}]*)}", custom, re.I)
    inside = m.group(1) if m else custom
    t = re.search(r"\btype\s*:\s*([^;\s}]+)", inside, re.I)
    return t.group(1).strip() if t else None


def extract_text(node: Optional[ET.Element]) -> Optional[str]:
    if node is None:
        return None
    text_equiv = find_first(node, "TextEquiv")
    unicode_el = find_first(text_equiv, "Unicode")
    if unicode_el is not None and len(unicode_el) == 0 and unicode_el.text:
        return unicode_el.text.strip() or None
    if unicode_el is not None and unicode_el.text:
        return unicode_el.text.strip() or None
    return None


# ---------------- Annotation builder ----------------

def Annotation(
        *,
        id: str,
        granularity: Optional[str] = None,
        canvas_id: Optional[str] = None,
        svg_path: Optional[str] = None,
        targets: Optional[List[str]] = None,
        body_text: Optional[str] = None,
        body_classification: Optional[str] = None,
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
    if canvas_id and svg_path:
        target.append({
            "type": "SpecificResource",
            "source": canvas_id,
            "selector": {"type": "SvgSelector", "value": svg_path},
        })
    for t in targets or []:
        target.append({"id": t, "type": "Annotation"})

    anno = {
        "type": "Annotation",
        "id": id,
        "motivation": "supplementing" if body_text else "highlighting",
        "textGranularity": granularity,
    }
    if granularity == "page":
        anno["purpose"] = "transcription-normalized"
        target.append({"type": "Canvas", "id": canvas_id})
    if granularity == "page-htr":
        anno["textGranularity"] = "page"
        anno["purpose"] = "transcription-diplomatic"
        target.append({"type": "Canvas", "id": canvas_id})
    if body:
        anno["body"] = body
    if target:
        anno["target"] = target
    return anno


# ---------------- Main converter ----------------


def convert_pagexml_to_web_annotations(
        xml_string: str,
        canvas_id: str,
        page_text: str = "",
        script_path: str = "",
        commit_id: Optional[str] = None
) -> Dict[str, Any]:
    annotations = []

    doc = ET.fromstring(xml_string)

    # Root elements
    page = find_first(doc, "Page")
    page_filename = get_attr(page, "imageFilename")
    width = int(get_attr(page, "imageWidth") or 0) or None
    height = int(get_attr(page, "imageHeight") or 0) or None

    base = re.sub(r"\.[a-zA-Z]+$", "", page_filename or "page")
    ap_uri = uf.annotation_page_url(uf.AnnotationPageType.TRANSCRIPTIONS, base)
    # base_id = (f"{URI_BASE_PATTERN}annotations:transcriptions:{urllib.parse.quote(base)}")

    block_idx = line_idx = word_idx = 0
    page_anno_id = f"{ap_uri}#page-normalized"
    text_lines: List[str] = []

    # Regions
    for region in find_all(page, "TextRegion"):
        block_idx += 1
        region_coords = find_first(region, "Coords")
        region_points = get_attr(region_coords, "points")
        region_svg = points_to_svg_path(region_points)
        region_id_raw = get_attr(region, "id") or f"block{block_idx}"
        block_anno_id = f"{ap_uri}#{urllib.parse.quote(region_id_raw)}"

        if region_svg:
            annotations.append(
                Annotation(
                    id=block_anno_id,
                    granularity="block",
                    canvas_id=canvas_id,
                    svg_path=region_svg,
                    body_classification=get_region_type(region),
                    targets=[page_anno_id],
                )
            )

        # Lines
        for line in find_all(region, "TextLine"):
            line_idx += 1
            line_coords = find_first(line, "Coords")
            line_points = get_attr(line_coords, "points")
            line_svg = points_to_svg_path(line_points)
            line_text = extract_text(line)
            line_id_raw = get_attr(line, "id") or f"line{line_idx}"
            line_anno_id = f"{ap_uri}#{urllib.parse.quote(line_id_raw)}"

            if line_text:
                text_lines.append(line_text)

            if line_svg or line_text:
                annotations.append(
                    Annotation(
                        id=line_anno_id,
                        granularity="line",
                        canvas_id=canvas_id,
                        svg_path=line_svg,
                        targets=[block_anno_id],
                        body_text=line_text,
                    )
                )

            # Words
            for w in find_all(line, "Word"):
                word_idx += 1
                w_coords = find_first(w, "Coords")
                w_points = get_attr(w_coords, "points")
                word_svg = points_to_svg_path(w_points)
                w_text = extract_text(w)
                word_id_raw = get_attr(w, "id") or f"word{word_idx}"
                word_anno_id = f"{ap_uri}#{urllib.parse.quote(word_id_raw)}"

                if word_svg or w_text:
                    annotations.append(
                        Annotation(
                            id=word_anno_id,
                            granularity="word",
                            canvas_id=canvas_id,
                            svg_path=word_svg,
                            targets=[line_anno_id],
                            body_text=w_text,
                        )
                    )

    # Page
    annotations.append(
        Annotation(
            id=page_anno_id,
            granularity="page",
            canvas_id=canvas_id,
            body_text=page_text,
        )
    )
    annotations.append(
        Annotation(
            id=page_anno_id.replace("normalized", "htr"),
            granularity="page-htr",
            canvas_id=canvas_id,
            body_text="\n".join(text_lines),
        )
    )

    # page_json_id = (
    #         "https://globalise-huygens.github.io/document-view-sandbox/iiif/annotations/transcriptions/"
    #         + re.sub(r"\.jpg$", ".json", page_filename or "", flags=re.I)
    # )

    if not commit_id:
        commit_id = git.read_current_commit_id(warn_on_uncommitted_changes=True)
    cf = CreatorFactory(script_paths=[script_path], commit_id=commit_id)
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

    if canvas_id and width and height:
        annotation_page["partOf"] = {
            "id": canvas_id,
            "type": "Canvas",
            "height": height,
            "width": width,
        }

    return annotation_page


def get_word_offsets(xml_string: str) -> Dict[str, Offset]:
    doc = ET.fromstring(xml_string)

    # Root elements
    page = find_first(doc, "Page")
    word_idx = 0
    htr_word_offset = {}
    offset = 0

    for region in find_all(page, "TextRegion"):
        for line in find_all(region, "TextLine"):
            for w in find_all(line, "Word"):
                word_idx += 1
                w_text = extract_text(w)
                w_len = len(w_text)
                word_id_raw = get_attr(w, "id") or f"word{word_idx}"
                htr_word_offset[word_id_raw] = Offset(offset, offset + w_len)
                offset += w_len + 1

    return htr_word_offset
