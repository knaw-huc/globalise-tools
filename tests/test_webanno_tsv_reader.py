import unittest

from globalise_tools.webanno_tsv_reader import read_webanno_tsv


class WebAnnoTsvReaderCase(unittest.TestCase):
    def test_reader_finds_format(self):
        path = '../data/inception_output/NL-HaNA_1.04.02_1092_0017_0021.tsv'
        doc = read_webanno_tsv(path)
        self.assertEqual(doc.format, "WebAnno TSV 3.3")  # add assertion here


if __name__ == '__main__':
    unittest.main()
