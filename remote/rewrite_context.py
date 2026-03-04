#!/usr/bin/env python3
# rewrite_context.py
import json
import sys

FILE_PREFIX = "file:///data/globalise-data/annotation-lists/data/contexts"
MAPPING = {
    "http://iiif.io/api/presentation/3/context.json": f"{FILE_PREFIX}/context.json",
    "http://www.w3.org/ns/anno.jsonld": f"{FILE_PREFIX}/anno.jsonld",
    "https://linked.art/ns/v1/linked-art.json": f"{FILE_PREFIX}/linked-art.json",
    "https://ns.huc.knaw.nl/globalise.jsonld": f"{FILE_PREFIX}/globalise.jsonld",
    "https://objectstore.surf.nl/87435b768620494e8e911c83d1997f24:globalise-data/contexts/aaao.json": f"{FILE_PREFIX}/aaao.json",
    "https://objectstore.surf.nl/87435b768620494e8e911c83d1997f24:globalise-data/contexts/crmdig.json": f"{FILE_PREFIX}/crmdig.json"
}


def rewrite(ctx):
    if isinstance(ctx, str):
        return MAPPING.get(ctx, ctx)
    if isinstance(ctx, list):
        return [rewrite(c) for c in ctx]
    return ctx


data = json.load(sys.stdin)
if "@context" in data:
    data["@context"] = rewrite(data["@context"])
print(json.dumps(data))
