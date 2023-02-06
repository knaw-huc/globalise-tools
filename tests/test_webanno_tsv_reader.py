import json
import unittest

from globalise_tools.webanno_tsv_reader import read_webanno_tsv, _split_dict


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)


class WebAnnoTsvReaderCase(unittest.TestCase):
    def test_reader_finds_format(self):
        path = '../data/inception_output/NL-HaNA_1.04.02_1092_0017_0021.tsv'
        doc = read_webanno_tsv(path)
        self.assertEqual(doc.format, "WebAnno TSV 3.3")
        self.assertEqual(doc.sentences[10].text, "Qulans")

        annotations_with_links = [a for a in doc.annotations if a.linked_annotations]
        for annotation in annotations_with_links:
            print(annotation.text)
            print(json.dumps(annotation, indent=4, cls=MyEncoder))
            for al in annotation.linked_annotations:
                print(f"{al.label}:")
                linked_annotation = doc.get_annotation_by_id(al.annotation_id)
                print(json.dumps(linked_annotation, indent=4, cls=MyEncoder))

    def test_split_dict(self):
        source = {
            "field1": "value 1.1|value 1.2",
            "field2": "value 2.1|value 2.2"
        }
        expected = [
            {
                "field1": "value 1.1",
                "field2": "value 2.1"
            },
            {
                "field1": "value 1.2",
                "field2": "value 2.2"
            }
        ]
        result = _split_dict(source)
        self.assertListEqual(expected, result)


if __name__ == '__main__':
    unittest.main()
