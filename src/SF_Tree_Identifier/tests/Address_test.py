import logging
import unittest
import os
import sys
from pathlib import Path # if you haven't already done so

file = Path(os.path.dirname(__file__)).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

# Additionally remove the current file's directory from sys.path
try:
    sys.path.remove(str(parent))
except ValueError: # Already removed
    pass
from SF_Tree_Identifier import Address

logging.basicConfig(level=logging.ERROR)

class AddressErrorsTestCase(unittest.TestCase):
    def test_too_short_address(self):
        with self.assertRaises(Address.AddressLengthError):
            Address.Address('123 Short')

    def test_non_int_street_number(self):
        with self.assertRaises((Address.NonIntegerStreetNumberError)):
            Address.Address('12d Street St')

    def test_bad_street(self):
        streets = Address.load_street_names()

        with self.assertRaises((Address.NoCloseMatchError)):
            address = Address.Address('12 bad St')
            Address.match_closest_street_name(address, streets)
class NewAddressTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.address = Address.Address('123 Street St')

    def test_street_number(self):
        self.assertTrue(self.address.street_number == '123')

    def test_street_name(self):
        self.assertTrue(self.address.street_name == 'Street St')

    def test_street_type(self):
        self.assertTrue(self.address.street_type == 'St')

    def test_street_address(self):
        self.assertTrue(self.address.street_address == '123 Street St')

class StandardAddressTestCase(unittest.TestCase):
    def test_street_to_st(self):
        address = Address.Address('123 Example Street')
        abbreviated_address = Address.abbreviate_street_type(address)
        self.assertTrue(abbreviated_address.street_address.title() == '123 Example St')

    def test_street_to_ave(self):
        address = Address.Address('123 Example Avenue')
        abbreviated_address = Address.abbreviate_street_type(address)
        self.assertTrue(abbreviated_address.street_address.title() == '123 Example Ave')

    def test_format_numeric_street(self):
        address = Address.Address('123 2nd St')
        address.format_numeric_street_name()
        self.assertTrue(address.street_address == '123 02nd St')

    def test_remove_city(self):
        address_input = '123 Example St, San Francisco'
        removed_city_address = Address.remove_city(address_input)
        self.assertTrue(removed_city_address == '123 Example St')

    def test_remove_city_no_comma(self):
        address_input = '123 Example St San Francisco'
        removed_city_address = Address.remove_city(address_input)
        self.assertTrue(removed_city_address == '123 Example St')

    def test_valid_input_not_changed(self):
        address_input = '123 Example St'
        removed_city_address = Address.remove_city(address_input)
        self.assertTrue(removed_city_address == '123 Example St')

    def test_random_comma(self):
        address_input = '123 Example, St'
        removed_city_address = Address.remove_city(address_input)
        self.assertTrue(removed_city_address == '123 Example St')

    def test_remove_city_and_zip(self):
        address_input = '123 Example St, San Francisco, CA 94110'
        removed_city_address = Address.remove_city(address_input)
        self.assertTrue(removed_city_address == '123 Example St')

    def test_remove_punctuation(self):
        address_input = '123 Example St.'
        cleaned_address = Address.remove_punctuation(address_input)
        self.assertTrue(cleaned_address == '123 Example St')

    def test_remove_punctuation_dont_change_non_punctuated(self):
        address_input = '123 Example St'
        cleaned_address = Address.remove_punctuation(address_input)
        self.assertTrue(cleaned_address == '123 Example St')

    def test_remove_punctuation_with_exception(self):
        address_input = '123 Example-Example St.'
        cleaned_address = Address.remove_punctuation(address_input, '-')
        self.assertTrue(cleaned_address == '123 Example-Example St')

    def test_create_standard_Address(self):
        address_input = '123. Example-Example Street, San Francisco, CA 94110'
        address = Address.create_standard_Address(address_input)
        self.assertTrue(address.street_address == '123 example-example st')

class StreetMatchingTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.street_list = Address.load_street_names()

    def test_valencia_street(self):
        address = Address.Address('1468 valencia st')
        closest_match = Address.match_closest_street_name(address, self.street_list)
        self.assertTrue(closest_match.street_name == 'valencia st')

    def test_mistyped_name(self):
        address = Address.Address('1468 vaelncia st')
        closest_match = Address.match_closest_street_name(address, self.street_list)
        self.assertTrue(closest_match.street_name == 'valencia st')

    def test_trash_name(self):
        address = Address.Address('1468 vaelnci st')
        with self.assertRaises(Address.NoCloseMatchError):
            closest_match = Address.match_closest_street_name(address, self.street_list)

class GetAddressForQueryTestCase(unittest.TestCase):
    def test_good_address(self):
        user_input = '1468 Valencia Street, San Francisco'
        query_address = Address.get_Address_for_query(user_input)
        self.assertTrue(query_address.street_address == '1468 valencia st')

    def test_bad_address(self):
        user_input = '1468 Example Street, San Francisco'
        with self.assertRaises(Address.NoCloseMatchError):
            query_address = Address.get_Address_for_query(user_input)

    def test_michael_address(self):
        user_input = '272 Capp St, San Francisco, CA 94110'
        query_address = Address.get_Address_for_query(user_input)
        self.assertTrue(query_address.street_address == '272 capp st')

    def test_other_michael_address(self):
        user_input = '272 Capp Street San Francisco'
        query_address = Address.get_Address_for_query(user_input)
        self.assertTrue(query_address.street_address == '272 capp st')



if __name__ == '__main__':
    unittest.main()
