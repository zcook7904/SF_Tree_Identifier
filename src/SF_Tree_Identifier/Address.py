from dataclasses import dataclass

class Address:
    """Dataclass to represent address. str returns the street address as a string and
    len the number of elements in the street address."""
    street_address: str

    def __str__(self):
        return self.street_address

    def __len__(self):
        return len(self.get_address_as_list())

    def get_address_as_list(self):
        """Converts the inputted address to a list if it is in string form. Returns the address as a list"""
        address_list = self.street_address.split(' ')
        return address_list

    @property
    def street_number(self):
        return int(self.get_address_as_list()[0])

    @property
    def street_name(self):
        return ' '.join(self.get_address_as_list()[1:])

    @street_number.setter
    def street_number(self, new_number: int):
        street_name = self.street_name
        self.street_address = f'{new_number} {street_name}'

    @street_name.setter
    def street_name(self, new_name: str):
        street_number = self.street_number
        self.street_address = f'{street_number} {new_name}'

    def check_address_arg_length(self) -> bool:
        """ Returns false if the input address doesn't have at least 3 components"""
        arg_length = len(self)
        # make sure input is correct length, max 10 is arb...
        if arg_length < 3 or arg_length > 10:
            # Address should contain {number} {street_name} {street_suffix} at minimum
            return False
        return True

    def check_street_number(self) -> bool:
        """ Returns True if the street number is valid"""
        # ensure first input is an integer
        try:
            # should throw value error if street number cannot be returned
            isinstance(self.street_number, int)
            return True
        except ValueError:
            return False

    def format_street_name(self):
        """adds '0' to street name if street name is numeric, <10, and doesn't contain '0' (ex 9th st -> 09th st)"""
        street_name = self.street_name
        if street_name[0].isnumeric() and not street_name[1].isnumeric():
            new_street_name = '0' + street_name
            self.street_name = new_street_name
        return True

    def check_if_street_in_SF(self, acceptable_street_names: list[str]) -> bool:
        """Returns True if the street name is in the SF street name list"""

        return self.street_name.casefold() in (name.casefold() for name in acceptable_street_names)

    def process_address(self, SF_streets: list[str]):
        """ verify the user has given a real address and process the address into something manageable by
        the Google Maps api.
        Accepts list in format [number, street_name, street_type] and returns string of full postal address"""

        if not self.check_address_arg_length():
            raise Exception

        if not self.check_street_number():
            return 491

        # clean up street name
        self.format_street_name()

        street_abbreviation_dict = load_street_type_abbreviations()
        if self.get_address_as_list()[-1].lower() in street_abbreviation_dict.keys():
            street_type = self.street_name.rsplit(' ')[-1]
            abbreviated_street_type = street_abbreviation_dict[street_type.lower()]
            self.street_name = self.street_name.replace(street_type, abbreviated_street_type)
