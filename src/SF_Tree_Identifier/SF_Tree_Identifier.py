import logging
import sqlite3
import os
from collections import namedtuple

import pandas as pd

import Address

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_LOCATION = os.path.join(DATA_DIR, "SF_trees.db")

class NoTreeFoundError(Exception):
    """Raised if no tree is found at the given address."""
    pass

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

    return None


def get_species(key: str) -> tuple | None:
    """Queries the species table for the species matching the pass key. Returns the tuple (qSpecies, urlPath) if a species is found and returns None if none are found."""
    species_query = create_species_query(key)
    result = query_db(species_query)

    if result:
        result = result[0]  # should only be one species per key
        qSpecies = result[0]
        urlPaths = str(result[1])
        return qSpecies, urlPaths

    return None


def main(user_input: str, check_nearby: bool = True) -> pd.DataFrame | dict:
    """Main function that queries tree species from the given user_input. Returns a panda dataframe with the results."""
    # create an Address object from the given user input. Raises an exception if the input is not appropriate for the DB.
    try:
        query_address = Address.get_Address_for_query(user_input)
    except Address.NoCloseMatchError as err:
        raise Address.NoCloseMatchError(f"Address {user_input} not found in San Francisco") from err
    except Address.AddressError as err:
        raise Address.AddressError(
            f"Invalid address {user_input} entered, ensure proper street address is given."
        ) from err

    # namedtuple address_key to keep addresses and species keys together for later result formatting
    # SUGGEST may make more sense as dict(?)
    address_key = namedtuple("AddressKeys", ["address", "key"])
    address_keys = []
    species_keys = None

    # get all tree_ids at the query address
    species_keys = get_species_keys(query_address)

    # if there are trees there, make address/tree_id tuple (may change to dict)
    if not species_keys is None:
        for species_key in species_keys:
            address_keys.append(address_key(query_address.street_address, species_key))

    if species_keys is None and check_nearby:
        # if no trees at given address, will look next door (+2 or -2 street number i.e. 1470 and 1466 if given 1468)
        logging.warning("Couldn't find trees at given address, looking nearby...")
        steps = [-2, 4]

        for step in steps:
            query_address.street_number = int(query_address.street_number) + step
            species_keys = get_species_keys(query_address)
            if not species_keys is None:
                for species_key in species_keys:
                    address_keys.append(
                        address_key(query_address.street_address, species_key)
                    )

    if len(address_keys) == 0:
        raise NoTreeFoundError(f"Can't find any trees near entered street address {user_input}")

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

def create_output_dict(results: pd.DataFrame) -> list[dict]:
    """Creates a formatted list of string messages from main()'s results df."""
    queried_addresses = results.queried_address.unique()
    tree_dict = {}
    for address in queried_addresses:
        grouped_results = (
            results.loc[results.queried_address == address]
            .groupby(["qSpecies", "urlPath"])
            .count()
            .reset_index()
            .rename({"queried_address": "count"}, axis=1)
        )
        grouped_results[["scientific_name", "common_name"]] = (
            grouped_results.qSpecies.str.split("::", expand=True)
            .fillna("")
            .apply(lambda name: name.str.strip())
        )

        grouped_results = grouped_results.drop("qSpecies", axis=1)
        tree_dict.update({address: grouped_results.to_dict(orient="records")})
    return tree_dict


def get_trees(user_input: str) -> list[str]:
    """Takes a string address from a user and returns a dictionary of the format:
    {address_1: [{
                common_name: str,
                scientific_name: str,
                urlPath: str,
                count: str
                },{}...]
     address_2: [{}, ...]
     }."""

    try:
        tree_df = main(user_input)
    except (Address.AddressError, NoTreeFoundError) as err:
        raise err
    except Exception as err:
        raise err

    return create_output_dict(tree_df)


if __name__ == "__main__":
    print(get_trees("1204 19th St"))
