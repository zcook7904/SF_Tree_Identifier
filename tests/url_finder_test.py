import unittest
import os
import sys

# adds python module to path
path_to_append = os.path.join('.', 'src')
sys.path.append(path_to_append)
from url_finder import url_finder


class WikiFinderTestCase(unittest.TestCase):
    def test_good_name(self):
        self.assertTrue(url_finder.wiki_exists('Corymbia_ficifolia'))

    def test_bad_name(self):
        self.assertFalse(url_finder.wiki_exists('bad_name_123'))

class SelecTreeFinderTestCase(unittest.TestCase):
    def test_good_name(self):
        self.assertTrue(url_finder.selec_tree_number('Corymbia_ficifolia') == 540)

    def test_bad_name(self):
        with self.assertRaises(IndexError):
            url_finder.selec_tree_number('bad_name_123')

if __name__ == '__main__':
    unittest.main()
