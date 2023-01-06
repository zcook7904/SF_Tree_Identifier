import logging
import sqlite3
import os
import pickle
import pandas as pd

from SF_Tree_Identifier import Address

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_LOCATION = os.path.join(DATA_DIR, "SF_trees.db")
SF_TREES_PATH = os.path.join(DATA_DIR, "SF_trees.pkl")
SPECIES_PATH = os.path.join(DATA_DIR, "species_dict.pkl")

ADDRESS_BUFFER = 3
SEARCH_NEARBY = True
TREE_DICT = None
SPECIES_DICT = None


class NoTreeFoundError(Exception):
    """Raised if no tree is found at the given address."""

    pass


def load_dict(dict_path: str) -> dict:
    with open(dict_path, "rb") as fp:
        return pickle.load(fp)


def create_address_query(street_address: str) -> str:
    """Creates the sql query to retrieve the qSpecies keys for a specfic address. Returns the query as a string."""
    query = f"""
        SELECT qSpecies
        FROM addresses
        WHERE qAddress = '{street_address}'"""
    return query


def create_species_query(key: str) -> str:
    """Creates the sql query to retrieve the species and URL path for the species key. Returns the query as a string."""
    query = f"""
        SELECT qSpecies, urlPath
        FROM species
        WHERE "index" = {key}"""
    return query


def check_db_connection() -> bool:
    """Checks if the SF_Trees database exists. Returns True if so, or raises a FileNotFoundError if not."""
    data_dir = os.listdir(DATA_DIR)
    _, db_name = os.path.split(DB_LOCATION)
    if db_name in data_dir:
        return True

    raise FileNotFoundError(f"Can't find the tree database at {DB_LOCATION}")


def query_db(query: str, fetchall: bool = True):
    """General function to query the sqlite3 database at DB_LOCATION. Returns the results if they are found or None if there are none."""
    con = sqlite3.connect(DB_LOCATION)
    cur = con.cursor()
    result = cur.execute(query)

    if result:
        if fetchall:
            result = result.fetchall()
        else:
            result = result.fetchone()

    con.close()
    return result


def get_species_keys(street_address: str) -> list[str]:
    """Queries the sqlite3 database for the species keys found at the given address.
    Returns a list of the keys found keys. List will be empty if none are found"""
    address_query = create_address_query(street_address)
    results = query_db(address_query)
    keys = []

    if results:
        for result in results:
            keys.append(str(result[0]))

    return keys


def get_species(key: str) -> tuple | None:
    """Queries the species table for the species matching the passed key.
    Returns the tuple (qSpecies, urlPath) if a species is found and returns None if none are found."""
    species_query = create_species_query(key)
    result = query_db(species_query, fetchall=False)

    if result:
        result = result  # should only be one species per key
        qSpecies = result[0]
        urlPaths = str(result[1])
        return qSpecies, urlPaths

    return None


def get_address_species_keys(street_address: str) -> dict:
    """Returns a dict in the form of {street_address: [key1, key2, ...]} for the given street address.
    Will return an empty dict if no trees are found at that address."""
    address_species_keys = {}
    species_keys = get_species_keys(street_address)
    # get all tree_ids at the query address and store in

    if species_keys:
        address_species_keys.update({street_address: species_keys})

    return address_species_keys


def get_nearby_species_keys(query_address: Address.Address) -> dict:
    """Queries address nearby (-2 and +2 of the street number) to the given address.
    Will return a dict with TWO addresses if both nearby address have trees.
    Will return an empty dict if none are found at either."""
    address_species_keys = {}
    steps = [-2, 4]

    for step in steps:
        query_address.street_number = int(query_address.street_number) + step
        address_species_keys.update(
            get_address_species_keys(query_address.street_address)
        )

    return address_species_keys


def calculate_total_trees(address_species_keys: dict) -> int:
    """Calculates the total number of trees in the address_species_keys_dict"""
    total = 0
    for species_keys in address_species_keys.values():
        total += len(species_keys)

    return total


def address_species_keys_to_dataframe(
    address_species_keys: dict, street_name: str
) -> pd.DataFrame:
    """Converts the address_species_keys dict to a pandas dataframe."""
    # get total number of trees for empty df
    total_trees = calculate_total_trees(address_species_keys)

    # create an empty results dataframe with number of rows as address_keys
    results = pd.DataFrame(
        columns=["qSpecies", "urlPath", "queried_address"],
        index=[i for i in range(total_trees)],
    )

    # save results to df
    i = 0
    for street_number, species_keys in address_species_keys.items():
        address = Address.Address(str(street_number) + " " + street_name)
        for specie_key in species_keys:
            qSpecie, urlPath = get_species(specie_key)
            results.loc[i] = {
                "qSpecies": qSpecie,
                "urlPath": urlPath,
                "queried_address": address.street_address.title(),
            }
            i += 1

    return results


def get_species_keys(street_number: int, street_name: str):
    """Gets all of the species keys"""

    try:
        trees_on_street = TREE_DICT[street_name]
    except KeyError:
        raise Address.AddressError(
            f"Invalid {street_name} entered, ensure proper street address is given."
        )

    trees = {}

    try:
        trees[street_number] = trees_on_street[street_number]
    except KeyError:
        if not SEARCH_NEARBY:
            raise NoTreeFoundError

        max_street_number = street_number + ADDRESS_BUFFER
        min_street_number = street_number - ADDRESS_BUFFER
        original_street_number = street_number

        while street_number < max_street_number:
            street_number += 2
            try:
                trees[street_number] = trees_on_street[street_number]
                break
            except KeyError:
                pass

        street_number = original_street_number
        while street_number > min_street_number:
            street_number -= 2
            try:
                trees[street_number] = trees_on_street[street_number]
                break
            except KeyError:
                pass

    if not trees:
        raise NoTreeFoundError

    return trees

def get_species(species_key: str) -> tuple:
    """uses the passed species key to retrieve the url path and species name from the species dictionary.
    Returns (qSpecies, urlPath)"""

    try:
        return SPECIES_DICT[species_key]['qSpecies'], str(SPECIES_DICT[species_key]['urlPath'])
    except KeyError as err:
        raise KeyError(err)

def main(user_input: str, check_nearby: bool = True, tree_dict = None, species_dict = None) -> pd.DataFrame | dict:
    """Main function that queries tree species from the given user_input. Returns a panda dataframe with the results."""
    # create an Address object from the given user input. Raises an exception if the input is not appropriate for the DB.
    global TREE_DICT
    global SPECIES_DICT

    if not TREE_DICT and not tree_dict:
        TREE_DICT = load_dict(SF_TREES_PATH)
    elif not TREE_DICT and tree_dict:
        TREE_DICT = tree_dict

    if not SPECIES_DICT and not species_dict:
        SPECIES_DICT = load_dict(SPECIES_PATH)
    elif not SPECIES_DICT and species_dict:
        SPECIES_DICT = species_dict

    try:
        query_address = Address.get_Address_for_query(user_input)
    except Address.NoCloseMatchError as err:
        raise Address.NoCloseMatchError(
            f"Address {user_input} not found in San Francisco"
        ) from err
    except Address.AddressError as err:
        raise Address.AddressError(
            f"Invalid address {user_input} entered, ensure proper street address is given."
        ) from err

    try:
        address_species_keys = get_species_keys(
            int(query_address.street_number), query_address.street_name
        )
    except NoTreeFoundError:
        raise NoTreeFoundError(
            f"Can't find any trees near entered street address {user_input}"
        )
    except Address.AddressError as err:
        raise (err)

    return address_species_keys_to_dataframe(
        address_species_keys, query_address.street_name
    )


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


def get_trees(user_input: str, tree_dict=None, species_dict=None) -> list[str]:
    """Takes a string address from a user and returns a dictionary of the format:
    {address_1: [{
                common_name: str,
                scientific_name: str,
                urlPath: str,
                count: str
                },{}...]
     address_2: [{}, ...]
     }."""
    global TREE_DICT

    if tree_dict:
        TREE_DICT = tree_dict
    else:
        TREE_DICT = load_dict(SF_TREES_PATH)

    try:
        tree_df = main(user_input)
    except (Address.AddressError, NoTreeFoundError) as err:
        raise err
    except Exception as err:
        raise err
    return create_output_dict(tree_df)


def create_message(tree: dict) -> str:
    """Creates formatted messages for each tree."""

    if tree["common_name"] != "":
        first_line = (
            f"{tree['common_name'].title()} ({tree['scientific_name'].title()})"
        )
    else:
        first_line = f"{tree['scientific_name'].title()}"

    number = tree["count"]
    if number > 1:
        first_line = first_line + f": {tree['count']}"

    if tree["urlPath"] != 0:
        second_line = f"https://selectree.calpoly.edu/tree-detail/{tree['urlPath']}\n"
        return "\n".join([first_line, second_line])

    return first_line.append("\n")


def format_messages(results: dict) -> list[str]:
    """Creates a formatted list of string messages from SF_Tree_Identifer dict output."""
    queried_addresses = results.keys()
    messages = []

    for address in queried_addresses:

        if len(results[address]) == 1:
            address_line = f"Tree at {address}:\n"
            messages.append(address_line + create_message(results[address][0]))
        else:
            address_line = f"Trees at {address}:\n"
            messages.append(address_line + create_message(results[address][0]))

            for tree in results[address][1:]:
                messages.append(create_message(tree))

    return messages


def print_trees(trees: dict) -> list[str]:
    messages = format_messages(trees)

    for message in messages:
        print(message)


if __name__ == "__main__":
    print(get_trees("1204 19th St"))