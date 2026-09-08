import unittest
from datetime import datetime

from loguru import logger

from globalise_tools.tools import sliding_window_iter


class ToolTestCase(unittest.TestCase):
    def test_sliding_window(self):
        list = [0, 1, 2, 3]
        expected_triples = [(None, 0, 1), (0, 1, 2), (1, 2, 3), (2, 3, None)]
        triples = [i for i in sliding_window_iter(list, 3)]
        self.assertEqual(expected_triples, triples)


if __name__ == '__main__':
    unittest.main()
