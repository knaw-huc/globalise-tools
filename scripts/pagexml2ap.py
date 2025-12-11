#!/usr/bin/env python3
import json
import sys

from globalise_tools.pagexml_tools import convert_pagexml_to_web_annotations

# ---------------- CLI ----------------

def main():
    if len(sys.argv) != 4:
        print("Usage: python pagexml2wa.py <inputPath> <canvas_id> <outputPath>", file=sys.stderr)
        print("  inputPath : path to pagexml file")
        print("  canvas_id : id of the canvas to use")
        print("  outputPath: path to the annotation page file to create")
        sys.exit(1)

    input_path, canvas_id, output_path = sys.argv[1:4]

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            xml_string = f.read()
    except FileNotFoundError:
        print(f"Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    annotation_page = convert_pagexml_to_web_annotations(xml_string, canvas_id)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(annotation_page, f, indent=2, ensure_ascii=False)

    print(f"AnnotationPage written to {output_path}")


if __name__ == "__main__":
    main()
