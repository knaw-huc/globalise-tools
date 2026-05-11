#!/usr/bin/env python3
import argparse
import hashlib
import json
import os

from loguru import logger
from pyld.jsonld import requests_document_loader

from globalise_tools.logger_tools import log_writing_file, log_reading_file

CACHE_DIR = "/Users/bram/.context_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

default_loader = requests_document_loader()

anno_context = """
{
    "oa":      "http://www.w3.org/ns/oa#",
    "dc":      "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "dctypes": "http://purl.org/dc/dcmitype/",
    "foaf":    "http://xmlns.com/foaf/0.1/",
    "rdf":     "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs":    "http://www.w3.org/2000/01/rdf-schema#",
    "skos":    "http://www.w3.org/2004/02/skos/core#",
    "xsd":     "http://www.w3.org/2001/XMLSchema#",
    "iana":    "http://www.iana.org/assignments/relation/",
    "owl":     "http://www.w3.org/2002/07/owl#",
    "as":      "http://www.w3.org/ns/activitystreams#",
    "schema":  "http://schema.org/",
    
    "id":      {"@type": "@id", "@id": "@id"},
    "type":    {"@type": "@id", "@id": "@type"},
    
    "Annotation":           "oa:Annotation",
    "Dataset":              "dctypes:Dataset",
    "Image":                "dctypes:StillImage",
    "Video":                "dctypes:MovingImage",
    "Audio":                "dctypes:Sound",
    "Text":                 "dctypes:Text",
    "TextualBody":          "oa:TextualBody",
    "ResourceSelection":    "oa:ResourceSelection",
    "SpecificResource":     "oa:SpecificResource",
    "FragmentSelector":     "oa:FragmentSelector",
    "CssSelector":          "oa:CssSelector",
    "XPathSelector":        "oa:XPathSelector",
    "TextQuoteSelector":    "oa:TextQuoteSelector",
    "TextPositionSelector": "oa:TextPositionSelector",
    "DataPositionSelector": "oa:DataPositionSelector",
    "SvgSelector":          "oa:SvgSelector",
    "RangeSelector":        "oa:RangeSelector",
    "TimeState":            "oa:TimeState",
    "HttpRequestState":     "oa:HttpRequestState",
    "CssStylesheet":        "oa:CssStyle",
    "Choice":               "oa:Choice",
    "Person":               "foaf:Person",
    "Software":             "as:Application",
    "Organization":         "foaf:Organization",
    "AnnotationCollection": "as:OrderedCollection",
    "AnnotationPage":       "as:OrderedCollectionPage",
    "Audience":             "schema:Audience", 
    
    "Motivation":    "oa:Motivation",
    "bookmarking":   "oa:bookmarking",
    "classifying":   "oa:classifying",
    "commenting":    "oa:commenting",
    "describing":    "oa:describing",
    "editing":       "oa:editing",
    "highlighting":  "oa:highlighting",
    "identifying":   "oa:identifying",
    "linking":       "oa:linking",
    "moderating":    "oa:moderating",
    "questioning":   "oa:questioning",
    "replying":      "oa:replying",
    "reviewing":     "oa:reviewing",
    "assessing":     "oa:assessing",
    "tagging":       "oa:tagging",
    
    "auto":          "oa:autoDirection",
    "ltr":           "oa:ltrDirection",
    "rtl":           "oa:rtlDirection",
    
    "body":          {"@type": "@id", "@id": "oa:hasBody"},
    "target":        {"@type": "@id", "@id": "oa:hasTarget"},
    "source":        {"@type": "@id", "@id": "oa:hasSource"},
    "selector":      {"@type": "@id", "@id": "oa:hasSelector"},
    "state":         {"@type": "@id", "@id": "oa:hasState"},
    "scope":         {"@type": "@id", "@id": "oa:hasScope"},
    "refinedBy":     {"@type": "@id", "@id": "oa:refinedBy"},
    "startSelector": {"@type": "@id", "@id": "oa:hasStartSelector"},
    "endSelector":   {"@type": "@id", "@id": "oa:hasEndSelector"},
    "renderedVia":   {"@type": "@id", "@id": "oa:renderedVia"},
    "creator":       {"@type": "@id", "@id": "dcterms:creator"},
    "generator":     {"@type": "@id", "@id": "as:generator"},
    "rights":        {"@type": "@id", "@id": "dcterms:rights"},
    "homepage":      {"@type": "@id", "@id": "foaf:homepage"},
    "via":           {"@type": "@id", "@id": "oa:via"},
    "canonical":     {"@type": "@id", "@id": "oa:canonical"},
    "stylesheet":    {"@type": "@id", "@id": "oa:styledBy"},
    "cached":        {"@type": "@id", "@id": "oa:cachedSource"},
    "conformsTo":    {"@type": "@id", "@id": "dcterms:conformsTo"},
    "items":         {"@type": "@id", "@id": "as:items", "@container": "@list"},
    "partOf":        {"@type": "@id", "@id": "as:partOf"},
    "first":         {"@type": "@id", "@id": "as:first"},
    "last":          {"@type": "@id", "@id": "as:last"},
    "next":          {"@type": "@id", "@id": "as:next"},
    "prev":          {"@type": "@id", "@id": "as:prev"},
    "audience":      {"@type": "@id", "@id": "schema:audience"},
    "motivation":    {"@type": "@vocab", "@id": "oa:motivatedBy"},
    "purpose":       {"@type": "@vocab", "@id": "oa:hasPurpose"},
    "textDirection": {"@type": "@vocab", "@id": "oa:textDirection"},
    
    "accessibility": "schema:accessibilityFeature",
    "bodyValue":     "oa:bodyValue",
    "format":        "dc:format",
    "language":      "dc:language",
    "processingLanguage": "oa:processingLanguage",
    "value":         "rdf:value",
    "exact":         "oa:exact",
    "prefix":        "oa:prefix",
    "suffix":        "oa:suffix",
    "styleClass":    "oa:styleClass",
    "name":          "foaf:name",
    "email":         "foaf:mbox",
    "email_sha1":    "foaf:mbox_sha1sum",
    "nickname":      "foaf:nick",
    "label":         "rdfs:label",
    
    "created":       {"@id": "dcterms:created", "@type": "xsd:dateTime"},
    "modified":      {"@id": "dcterms:modified", "@type": "xsd:dateTime"},
    "generated":     {"@id": "dcterms:issued", "@type": "xsd:dateTime"},
    "sourceDate":    {"@id": "oa:sourceDate", "@type": "xsd:dateTime"},
    "sourceDateStart": {"@id": "oa:sourceDateStart", "@type": "xsd:dateTime"},
    "sourceDateEnd": {"@id": "oa:sourceDateEnd", "@type": "xsd:dateTime"},
    
    "start":         {"@id": "oa:start", "@type": "xsd:nonNegativeInteger"},
    "end":           {"@id": "oa:end", "@type": "xsd:nonNegativeInteger"},
    "total":         {"@id": "as:totalItems", "@type": "xsd:nonNegativeInteger"},
    "startIndex":    {"@id": "as:startIndex", "@type": "xsd:nonNegativeInteger"}
}
"""


def safe_filename_from_url(url: str) -> str:
    """Return a safe, unique filename for a given URL."""
    # Hash the URL to avoid illegal filename characters and length issues
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return f"{digest}.json"


from typing import Any


def disk_caching_loader(url: str, doc_loader) -> Any:
    if url == "https://www.w3.org/ns/anno.jsonld":
        with open(f"{CACHE_DIR}/anno.jsonld", "r", encoding="utf-8") as f:
            return json.load(f)

    """Document loader that caches JSON-LD contexts on disk."""
    cache_file = os.path.join(CACHE_DIR, safe_filename_from_url(url))

    # Use cache if it exists
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    # Otherwise, fetch it using pyld’s default loader
    logger.info(f"Fetching and caching context: {url}")
    doc = default_loader(url)

    # Store in cache
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)

    return doc


from rdflib import Graph


def export_in_ttl(ner_annotations: list, ttl_out_path: str) -> None:
    logger.info(f"reading annotations into rdf graph")
    as_jsonld = [json.dumps(wa).replace('"http://www.w3.org/ns/anno.jsonld"', anno_context) for wa in ner_annotations]
    g = Graph()
    for json_ld in as_jsonld:
        g.parse(data=json_ld, format="json-ld")
    log_writing_file(ttl_out_path)
    g.serialize(ttl_out_path, format="ttl")


from argparse import Namespace


@logger.catch
def get_arguments() -> Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Web Annotations to Turtle",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("json_path",
                        help="The path to the json file containing a list of web annotations",
                        type=str
                        )
    return parser.parse_args()


@logger.catch
def main() -> None:
    args = get_arguments()
    log_reading_file(args.json_path)
    # Tell pyld (and thus rdflib-jsonld) to use our caching loader
    with open(args.json_path, "r") as f:
        annotations = json.load(f)
    out_path = args.json_path.replace(".json", ".ttl")
    log_writing_file(out_path)
    export_in_ttl(annotations, out_path)


def main2() -> None:
    from pyld import jsonld

    def disk_caching_loader2(url, something_else):
        print(something_else)
        print("✅ Custom loader called for:", url)
        raise SystemExit("Test finished")  # stop early so it doesn’t fetch anything

    jsonld.set_document_loader(disk_caching_loader2)

    # Minimal JSON-LD that triggers a context load
    data = {"@context": "https://linked.art/ns/v1/linked-art.json", "@id": "x"}
    jsonld.expand(data)


if __name__ == '__main__':
    main()
