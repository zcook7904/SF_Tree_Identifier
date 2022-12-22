import logging
import os
import sys
import unittest

from pathlib import Path  # if you haven't already done so

file = Path(os.path.dirname(__file__)).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

# Additionally remove the current file's directory from sys.path
try:
    sys.path.remove(str(parent))
except ValueError:  # Already removed
    pass
from SF_Tree_Identifier import identify_trees


class DataTestCase(unittest.TestCase):
    def test_data_dir_exists(self):
        self.assertTrue(os.path.exists(identify_trees.DATA_DIR))

    def test_street_names_exist(self):
        data_files = os.listdir(identify_trees.DATA_DIR)
        self.assertTrue("street_names.json" in data_files)

    def test_street_types(self):
        data_files = os.listdir(identify_trees.DATA_DIR)
        self.assertTrue("street_types.json" in data_files)

    def test_db_exists(self):
        data_files = os.listdir(identify_trees.DATA_DIR)
        _, db_file_name = os.path.split(identify_trees.DB_LOCATION)
        self.assertTrue(db_file_name in data_files)

    def test_db_connects(self):
        def check_connection():
            query = f"""
            SELECT qSpecies
            FROM addresses
            WHERE qAddress = '1470 Valencia St'"""

            try:
                identify_trees.query_db(query)
                return True
            except Exception as err:
                logging.error(err)
                return False

        self.assertTrue(check_connection)


class PoorInputTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, True)  # add assertion here


class TotalTreeTestCase(unittest.TestCase):
    def test_one_tree(self):
        address_species_keys = {"1470 Valencia St": ["2"]}
        self.assertTrue(identify_trees.calculate_total_trees(address_species_keys) == 1)

    def test_two_trees(self):
        address_species_keys = {"1470 Valencia St": ["2", "25"]}
        self.assertTrue(identify_trees.calculate_total_trees(address_species_keys) == 2)


class GetTreesTestCase(unittest.TestCase):
    def test_valencia_address(self):
        user_input = "1470 Valencia St"
        intended_result = {
            "1470 Valencia St": [
                {
                    "urlPath": "1425",
                    "count": 1,
                    "scientific_name": "Lophostemon confertus",
                    "common_name": "Brisbane Box",
                }
            ]
        }
        self.assertTrue(identify_trees.get_trees(user_input) == intended_result)

    def test_brotherhood_address(self):
        user_input = "900 Brotherhood Way"
        intended_result = {
            "900 Brotherhood Way": [
                {
                    "urlPath": "476",
                    "count": 4,
                    "scientific_name": "Cupressus macrocarpa",
                    "common_name": "Monterey Cypress",
                },
                {
                    "urlPath": "1035",
                    "count": 2,
                    "scientific_name": "Pinus canariensis",
                    "common_name": "Canary Island Pine",
                },
                {
                    "urlPath": "1071",
                    "count": 12,
                    "scientific_name": "Pinus radiata",
                    "common_name": "Monterey Pine",
                },
            ]
        }
        print(identify_trees.get_trees(user_input))
        self.assertTrue(identify_trees.get_trees(user_input) == intended_result)

    def test_valencia_address(self):
        user_input = "1204 19th st"
        intended_result = {
            "1202 19Th St": [
                {
                    "urlPath": "1005",
                    "count": 1,
                    "scientific_name": "Photinia fraseri",
                    "common_name": "Photinia: Chinese photinia",
                }
            ],
            "1206 19Th St": [
                {
                    "urlPath": "925",
                    "count": 1,
                    "scientific_name": "Maytenus boaria",
                    "common_name": "Mayten",
                }
            ],
        }
        self.assertTrue(identify_trees.get_trees(user_input) == intended_result)

    def test_no_tree_address(self):
        user_input = "1466 Valencia St"
        with self.assertRaises(identify_trees.NoTreeFoundError):
            identify_trees.get_trees(user_input)


if __name__ == "__main__":
    unittest.main()
