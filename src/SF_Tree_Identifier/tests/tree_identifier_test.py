import os
import sys
import unittest

from pathlib import Path # if you haven't already done so

file = Path(os.path.dirname(__file__)).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

# Additionally remove the current file's directory from sys.path
try:
    sys.path.remove(str(parent))
except ValueError: # Already removed
    pass
from SF_Tree_Identifier import identify_trees

class DataTestCase(unittest.TestCase):
    def test_data_dir_exists(self):
        self.assertTrue(os.path.exists(identify_trees.DATA_DIR))

    def test_street_names_exist(self):
        data_files = os.listdir(identify_trees.DATA_DIR)
        self.assertTrue('street_names.json' in data_files)

    def test_street_types(self):
        data_files = os.listdir(identify_trees.DATA_DIR)
        self.assertTrue('street_types.json' in data_files)

    def test_db_exists(self):
        data_files = os.listdir(identify_trees.DATA_DIR)
        _, db_file_name = os.path.split(identify_trees.DB_LOCATION)
        self.assertTrue(db_file_name in data_files)

class PoorInputTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, True)  # add assertion here


if __name__ == '__main__':
    unittest.main()
