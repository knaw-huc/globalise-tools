import unittest

from icecream import ic

from globalise_tools.webanno_tsv_reader import read_webanno_tsv, _layer_field_names, _split_dict


class WebAnnoTsvReaderCase(unittest.TestCase):
    def test_reader_finds_format(self):
        path = '../data/inception_output/NL-HaNA_1.04.02_1092_0017_0021.tsv'
        doc = read_webanno_tsv(path)
        # ic(doc.__dict__)
        self.assertEqual(doc.format, "WebAnno TSV 3.3")
        self.assertEqual(doc.sentences[10].text, "Qulans")
        # self.assertEqual(doc.layers, [])
        layer_names = [l.name for l in doc.layers]
        ic(layer_names)

        layer_field_names = _layer_field_names(doc)

        # for t in doc.tokens:
        #     o = {"id": f"{t.sentence_num}-{t.token_num}"}
        #     for i, e in enumerate(t.extra):
        #         if e != "_":
        #             o[layer_field_names[i]] = e
        #     if len(o.items()) > 1:
        #         ic(o)

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
