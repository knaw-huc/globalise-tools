import uuid
from dataclasses import dataclass
from datetime import datetime
from json import JSONEncoder
from typing import Dict, Any

from dataclasses_json import dataclass_json
from pagexml.model.physical_document_model import Coords

import globalise_tools.tools as gt


@dataclass
class WebAnnotation:
    body: Dict[str, Any]
    target: Any

    def wrapped(self):
        anno_uuid = uuid.uuid4()
        return {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "id": f"urn:globalise:annotation:{anno_uuid}",
            "type": "Annotation",
            "motivation": "classifying",
            "generated": datetime.today().isoformat(),  # use last-modified from pagexml for px: types
            "generator": {  # use creator metadata from pagexml for px: types
                "id": "https://github.com/rvankoert/loghi-htr",
                "type": "Software",
                "name": "Loghi"
            },
            "body": self.body,
            "target": self.target
        }


@dataclass
class TRVersions:
    txt: str
    segmented: str
    conll: str


@dataclass_json
@dataclass
class GTToken:
    text: str
    text_with_ws: str
    offset: int


class AnnotationEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, gt.Annotation) \
                or isinstance(obj, gt.PXTextRegion) \
                or isinstance(obj, gt.PXTextLine) \
                or isinstance(obj, GTToken):
            return obj.to_dict()
        elif isinstance(obj, WebAnnotation):
            return obj.wrapped()
        elif isinstance(obj, Coords):
            return obj.points
