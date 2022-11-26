import logging
import sqlite3
import os
from timeit import timeit
from collections import namedtuple
import pandas as pd

import Address

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_LOCATION = os.path.join(DATA_DIR, "SF_Trees.db")


def create_address_query(address: Address.Address) -> str:
    """Creates the sql query to retrieve the qSpecies keys for a specfic address. Returns the query as a string."""
    query = f"""
        SELECT qSpecies
        FROM addresses
        WHERE qAddress = '{address.street_address}'"""
    return query


def create_species_query(key) -> str:
    """Creates the sql query to retrieve the species and URL path for the species key. Returns the query as a string."""
    query = f"""
        SELECT qSpecies, urlPath
        FROM species
        WHERE "index" = {key}"""
    return query


def query_db(query: str):
    """General function to query the sqlite3 database at DB_LOCATION. Returns the results if they are found or None if there are none."""
    con = sqlite3.connect(DB_LOCATION)
    cur = con.cursor()
    result = cur.execute(query)

    if result:
        result = result.fetchall()

    con.close()
    return result


def get_species_keys(address: Address.Address) -> list[str] | None:
    """Queries the sqlite3 database for the species keys found at the given address.
    Returns a list of the keys found keys or None if none are found."""
    address_query = create_address_query(address)
    results = query_db(address_query)

    if results:
        keys = []
        for result in results:
            keys.append(str(result[0]))
        return keys
    else:
        return None


def get_species(key: str) -> tuple | None:
    species_query = create_species_query(key)
    result = query_db(species_query)

    if result:
        result = result[0]  # should only be one species per key
        qSpecies = result[0]
        urlPaths = str(result[1])
        return qSpecies, urlPaths

    else:
        return None


def main(user_input: str, check_nearby: bool = True) -> pd.DataFrame:
    """Main function that queries tree species from the given user_input. Returns a panda dataframe with the results."""
    # create an Address object from the given user input. Raises an exception if the input is not appropriate for the DB.
    try:
        query_address = Address.get_Address_for_query(user_input)
    except Address.NoCloseMatchError:
        raise Exception("Address not found in San Francisco")
    except Address.AddressError as err:
        raise Exception(
            "Invalid address entered, ensure proper street address is given."
        )

    # namedtuple address_key to keep addresses and species keys together for later result formatting
    address_key = namedtuple("AddressKeys", ["address", "key"])
    address_keys = []
    keys = None

    keys = get_species_keys(query_address)

    if not keys is None:
        for key in keys:
            address_keys.append(address_key(query_address.street_address, key))

    if keys is None and check_nearby:
        # if no trees at given address, will look next door (+2 or -2 street number i.e. 1470 and 1466 if given 1468)
        logging.warning(f"Couldn't find trees at given address, looking nearby...")
        steps = [-2, 4]

        for step in steps:
            query_address.street_number = int(query_address.street_number) + step
            keys = get_species_keys(query_address)
            if not keys is None:
                for key in keys:
                    address_keys.append(address_key(query_address.street_address, key))

    if len(address_keys) == 0:
        raise Exception(f"Can't find any trees near entered street number")

    # create an empty results dataframe with number of rows as address_keys
    results = pd.DataFrame(
        columns=["qSpecies", "urlPath", "queried_address"],
        index=[i for i in range(len(address_keys))],
    )

    # save results to df
    for i, item in enumerate(address_keys):
        qSpecie, urlPath = get_species(item.key)
        results.loc[i] = {
            "qSpecies": qSpecie,
            "urlPath": urlPath,
            "queried_address": item.address.title(),
        }

    return results


def create_message(tree: pd.Series, number: int):

    scientific_name, common_name = split_qSpecies(tree.qSpecies)

    if not common_name is None:
        first_line = f"{common_name.title()} ({scientific_name.title()})"
    else:
        first_line = f'{scientific_name.title()}'

    if number > 1:
        first_line = first_line + f": {number}"

    if tree.urlPath != 0:
        second_line = f"https://selectree.calpoly.edu/tree-detail/{tree.urlPath}\n"
        return "\n".join([first_line, second_line])
    else:
        return first_line.append("\n")

def split_qSpecies(qSpecies: str) -> tuple:
    split_species = qSpecies.split(' :: ')
    if len(split_species) == 1:
        scientific_name = split_species[0].replace(' ::', '')
        common_name = None
    else:
        scientific_name, common_name = split_species

    return scientific_name, common_name

def format_output(results: pd.DataFrame) -> list[str]:
    queried_addresses = results.queried_address.unique()
    messages = list()

    for address in queried_addresses:
        address_line = f'Trees at {address}:\n'
        num_species = len(results.qSpecies.unique())

        if len(results) == 1:
            address_line = f'Tree at {address}:\n'
            messages.append(address_line + create_message(results.iloc[0], 1))

        elif num_species == 1:
            messages.append(address_line + create_message(results.iloc[0], len(results)))

        else:
            grouped_results = results.groupby(['qSpecies', 'urlPath']).count().reset_index().rename({'queried_address': 'count'}, axis=1)
            first_message = messages.append(address_line + create_message(grouped_results.iloc[0], grouped_results.loc[0, 'count']))

            for tree in grouped_results[1:].itertuples():
                messages.append(create_message(tree, tree.count))

    return messages


if __name__ == "__main__":
    results = main('1468 Valencia St')
    formatted_results = format_output(results)

    for message in formatted_results:
        print(message)


# if __name__ == "__main__":
#     main('900 Brotherhood Way').to_csv('brotherhood.csv')
