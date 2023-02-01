from dataclasses import dataclass


@dataclass
class WATDocument:
    format: str = ""


PREFIX_FORMAT = "#FORMAT="


def read_webanno_tsv(path: str) -> WATDocument:
    doc = WATDocument()
    with open(path, mode='r', encoding='utf-8') as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if line.startswith(PREFIX_FORMAT):
            doc.format = line.replace(PREFIX_FORMAT, "")
    return doc
