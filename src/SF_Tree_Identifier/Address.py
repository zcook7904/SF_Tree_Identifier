import logging
import os
import json
import re
from string import punctuation as PUNCTUATION

from dataclasses import dataclass
from thefuzz import process as fuzz_process

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

##TODO add broadway edge case


class AddressError(Exception):
    """Base Exception for errors related to the Address class"""

    pass


class AddressLengthError(AddressError):
    """Error raised when an entered address does not contain at least 3 elements"""

    pass


class NonIntegerStreetNumberError(AddressError):
    """Error raise when an entered street number is not an integer."""


class NoCloseMatchError(Exception):
    """Error raised when no close match is found in match_closest_street_name"""


class Address:
    """Dataclass to represent address. str returns the street address as a string and
    len the number of elements in the street address."""

    street_number: str
    street_name: str

    def __init__(self, street_address: str, raise_invalid_error: bool = True):
        street_address_list = street_address.split(" ")

        self.street_number = street_address_list[0]

        self.street_name = " ".join(street_address_list[1:])

        if raise_invalid_error:
            self.is_valid_address(raise_error=True)

    def __str__(self):
        return self.street_address

    def __len__(self):
        return len(self.get_address_as_list())

    def get_address_as_list(self):
        """Converts the inputted address to a list if it is in string form. Returns the address as a list"""
        address_list = self.street_address.split(" ")
        return address_list

    @property
    def street_type(self):
        return self.street_name.split(" ")[-1]

    @property
    def street_address(self):
        return f"{self.street_number} {self.street_name}"

    def check_address_arg_length(self) -> bool:
        """Returns false if the input address doesn't have at least 3 components"""
        arg_length = len(self)
        if arg_length < 3:
            # Address should contain {number} {street_name} {street_suffix} at minimum
            raise AddressLengthError(
                f"Street address {self.street_address} does not contain enough elements (number name type)"
            )
        else:
            return True

    def check_street_number(self) -> bool:
        """Returns True if the street number is valid"""
        # ensure first input is an integer
        try:
            # should throw value error if street number cannot be returned
            int(self.street_number)
            return True
        except ValueError:
            raise NonIntegerStreetNumberError(
                f"{self.street_number} is not a valid numeric street number"
            )

    def format_numeric_street_name(self):
        """adds '0' to street name if street name is numeric, <10, and doesn't contain '0' (ex 9th st -> 09th st)"""
        street_name = self.street_name
        if street_name[0].isnumeric() and not street_name[1].isnumeric():
            new_street_name = "0" + street_name
            self.street_name = new_street_name
        return True

    def is_valid_address(self, raise_error: bool = False):
        """Verifies an the Address object is a valid street address and returns true if it is.
        If raise_error is false(default), an invalid address will return False. If raise_error is passed as True,
        the method will raise the corresponding error."""

        try:
            self.check_address_arg_length()
        except AddressLengthError as err:
            if raise_error:
                raise AddressLengthError(err)
            else:
                logging.warning(f"Excepted error: {err}")
                return False

        try:
            self.check_street_number()
        except NonIntegerStreetNumberError as err:
            if raise_error:
                raise NonIntegerStreetNumberError(err)
            else:
                logging.warning(f"Excepted error: {err}")
                return False

        return True


def load_street_type_abbreviations(
    path: str = os.path.join(DATA_DIR, "street_types.json")
) -> dict:
    """Loads the street type dictionary json file and returns it as a dict. Raises FileNotFoundError if the file is not found."""
    try:
        with open(path, "r") as fp:
            street_type_dict = json.load(fp)
            return street_type_dict
    except FileNotFoundError:
        raise FileNotFoundError(
            f"street_type_dict_file not found at {os.path.abspath(path)}"
        )


def remove_city(address_input: str) -> str:
    """Removes the city/state/zipcode from an inputted string address and returns only the street address. If there
    is no city/state/zipcode info, the original string is returned. *only works for San Francisco*"""

    address_list = address_input.split(",")

    if len(address_list) > 1:
        if Address(address_list[0], raise_invalid_error=False).is_valid_address():
            return address_list[0]

        else:
            address_input = address_input.replace(",", "")

    search = re.search("San Francisco", address_input, re.IGNORECASE)

    if search:
        address = address_input.split(search.group())[0]
        address = address.strip()
    else:
        address = address_input

    return address


def abbreviate_street_type(address: Address) -> Address:
    """Abbreviates the street type if it is in it's long form (i.e. street -> st). Returns a new Address object.
    If the address cannot or does not need to be abbreviated, the original Address is returned."""

    # load the street_type_dictionaries
    try:
        street_abbreviation_dict = load_street_type_abbreviations()
    except FileNotFoundError as err:
        logging.error(f"{err}: street not abbreviated.")
        return address

    street_type = address.street_type.lower()

    if street_type in street_abbreviation_dict.keys():
        # get the corressponding abbreviated street type and create a new street name string with the long type replaced
        abbreviated_street_type = street_abbreviation_dict[street_type]
        new_street_name = address.street_name.replace(
            address.street_type, abbreviated_street_type
        )
        # create a new Address
        abbreviated_address = Address(f"{address.street_number} {new_street_name}")
        return abbreviated_address

    # if the street type is not found in the dict, return the original address
    else:
        return address


def remove_punctuation(input: str, *exceptions: str) -> str:
    """Removes all PUNCTUATION from a string and returns the stripped string.
    Excepts exceptions from PUNCTUATION removal."""
    allowed_punctuation = PUNCTUATION
    for exception in exceptions:
        allowed_punctuation = allowed_punctuation.replace(exception, "")

    allowed_punctuation_set = re.compile(f"[{re.escape(allowed_punctuation)}]")
    return allowed_punctuation_set.sub("", input)


def create_standard_Address(user_input: str) -> Address:
    """Takes a user string input and creates a 'standard' Address object.
    This entails:
        - Street address only
        - Lower case
        - No random puncuation
        - Abbreviated street type
    Returns the standard Address. Will raise corresponding errors if users input is invalid."""

    address_string = user_input.lower().strip()
    address_string = remove_city(address_string)
    address_string = remove_punctuation(address_string, "-")
    address = Address(address_string)
    address = abbreviate_street_type(address)
    return address


def load_street_names(path: str = os.path.join(DATA_DIR, "street_names.json")) -> list:
    """Loads and returns list of street names in SF Tree Database."""
    try:
        with open(path, "r") as fp:
            street_names = json.load(fp)
            return street_names
    except FileNotFoundError:
        raise FileNotFoundError(
            f"street_names file not found at {os.path.abspath(path)}"
        )


def match_closest_street_name(
    address: Address, streets: list[str], min_score: int = 90
) -> Address:
    """Match the Address objects street name to a queryable street name in streets (from SF_Trees.db).
    If perfect match, the original Address will be returned.
    If there is a match with a score greater than min_score, a new Address object with that matched street name will be returned.
    If no close match is found, NoCloseMatchError is raised."""

    street_name = address.street_name

    if street_name in streets:
        return address

    closest_match, score = fuzz_process.extractOne(
        street_name, streets
    )  # specify method
    if score > min_score:
        address.street_name = closest_match
        return address
    raise NoCloseMatchError(
        f"Street name match for {address.street_name} doesn't meet minimum score of {min_score}. "
        f"{closest_match=} {score=}"
    )


def get_Address_for_query(user_input: str) -> Address:
    address = create_standard_Address(user_input)
    street_names = load_street_names()
    return match_closest_street_name(address, street_names)
