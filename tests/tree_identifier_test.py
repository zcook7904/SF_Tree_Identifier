import os.path
import unittest

import SF_Tree_Identifier


class DataTestCase(unittest.TestCase):
    def test_data_dir_exists(self):
        self.assertTrue(os.path.exists(SF_Tree_Identifier.DATA_DIR))

    def test_street_names_exist(self):
        data_files = os.listdir(SF_Tree_Identifier.DATA_DIR)
        self.assertTrue('street_names.json' in data_files)

    def test_street_types(self):
        data_files = os.listdir(SF_Tree_Identifier.DATA_DIR)
        self.assertTrue('street_types.json' in data_files)

    def test_db_exists(self):
        data_files = os.listdir(SF_Tree_Identifier.DATA_DIR)
        _, db_file_name = os.path.split(SF_Tree_Identifier.DB_LOCATION)
        self.assertTrue(db_file_name in data_files)

class PoorInputTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, True)  # add assertion here


if __name__ == '__main__':
    unittest.main()
