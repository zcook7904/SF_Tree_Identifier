import unittest
import os
import sys
import pandas as pd

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

class AssignUrlTestCase(unittest.TestCase):
    def test_url_assigned(self):
        species = pd.Series(['Corymbia ficifolia :: Red Flowering Gum', 'bad name 123 :: worse name'], name='qSpecies', dtype='string')
        assigned_species = url_finder.assign_url_paths(species)
        self.assertTrue(assigned_species.iloc[0, 1] == 540)

if __name__ == '__main__':
    unittest.main()
