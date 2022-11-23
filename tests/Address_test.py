import logging
import unittest
import os
import sys

# adds python module to path
path_to_append = os.path.join('.', 'src')
sys.path.append(path_to_append)
from SF_Tree_Identifier import Address

logging.basicConfig(level=logging.ERROR)

class AddressErrorsTestCase(unittest.TestCase):
    def test_too_short_address(self):
        with self.assertRaises(Address.AddressLengthError):
            Address.Address('123 Short')

    def test_non_int_street_number(self):
        with self.assertRaises((Address.NonIntegerStreetNumberError)):
            Address.Address('12d Street St')


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

if __name__ == '__main__':
    unittest.main()
