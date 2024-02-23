import unittest

import pagexml.parser as px
from icecream import ic


class ProcessedPageXMLTestCase(unittest.TestCase):
    def test_original(self):
        file_path = "../.local/NL-HaNA_1.04.02_1053_0001.xml"
        self._process_pagexml(file_path)

    def test_example(self):
        file_path = "../.local/NL-HaNA_1.04.02_1053_0001_example.xml"
        self._process_pagexml(file_path)

    def _process_pagexml(self, file_path):
        doc = px.parse_pagexml_file(file_path)
        ic(doc.metadata)
        for tr in doc.text_regions:
            for line in tr.lines:
                ic(line.text)
        self.assertEqual(None, doc.text)


if __name__ == '__main__':
    unittest.main()
