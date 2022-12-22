import sqlite3
import pandas as pd
import os
import logging
import time

os.chdir(os.path.dirname(__file__))
TREE_LIST_PATH = os.path.join("..", "Cleaned_Street_Tree_List.csv")
MAPPED_SPECIES_PATH = os.path.join("..", "mapped_species.csv")
DB_PATH = os.path.join("..", "SF_trees.db")


def load_original_data(path: str) -> pd.DataFrame:
    """Loads the original data csv and returns a pandas dataframe of the csv file."""
    try:
        return pd.read_csv(path, index_col=0)
    except FileNotFoundError:
        raise FileNotFoundError(f"Cannot find {os.path.abspath(path)}")


def species_difference(species_list_1: list, species_list_2: list) -> set:
    """Determines if a species from list 1 is not in list 2. Returns the set of the difference"""
    address_species_set = set(species_list_1)
    mapped_species_set = set(species_list_2)
    return address_species_set.difference(mapped_species_set)


def get_db_tables(db_path: str) -> list[str]:
    """Returns a list of every table in the given db."""
    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        query = """
        SELECT name FROM sqlite_schema
        WHERE type='table'; """

        results = cur.execute(query).fetchall()

    result_list = [None] * len(results)
    for i, result in enumerate(results):
        result_list[i] = result[0]

    return result_list

def get_db_indicies(db_path: str) -> list[str]:
    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        query = """
        SELECT name 
        FROM sqlite_master 
        WHERE type = 'index';
         """

        results = cur.execute(query).fetchall()

    result_list = [None] * len(results)
    for i, result in enumerate(results):
        result_list[i] = result[0]

    return result_list


def make_table(
    df: pd.DataFrame, schema: str, table_name: str, db_path: str, overwrite: bool = False
) -> None:
    """Generic function to create a new table in the given db. If overwrite is True, the function will overwrite the table if it already exists. Else, the function will not overwrite the table."""
    if table_name in get_db_tables(db_path) and not overwrite:
        logging.warning(
            f"Table {table_name} already exists in {db_path} and overwrite is False; skipping table creation."
        )
        return None

    elif table_name in get_db_tables(db_path):
        logging.warning(
            f"Table {table_name} already exists in {db_path} but is being overwritten."
        )

    with sqlite3.connect(db_path) as con:

        cur = con.cursor()
        result = cur.execute(schema)

        df.to_sql(table_name, con, if_exists="append")

def make_species_table(species_df: pd.DataFrame, db_path: str) -> None:
    """Creates the species table in the sqlite3 database and saves the species df to it.
    Uses the index as the primary key.
    The index number also corresponds to the qSpecies column in the corresponding address/tree table."""

    table_name = 'species'
    schema = f"""
    CREATE TABLE "{table_name}" (
    "index" INTEGER PRIMARY KEY NOT NULL,
      "qSpecies" TEXT NOT NULL,
      "urlPath" INTEGER(0) NOT NULL 
    )
    """

    make_table(species_df, schema, table_name, db_path)

def make_address_table(address_df: pd.DataFrame, db_path: str, sort: bool = True) -> None:
    """Makes the address table containing all trees and their corresponding address and species_key"""

    if sort:
        address_df = address_df.sort_values('qAddress')

    table_name = 'addresses'
    schema = f"""
    CREATE TABLE "{table_name}" (
    "TreeID" INTEGER PRIMARY KEY,
    "qAddress" TEXT,
    "qSpecies" INTEGER,
    "SiteOrder" INTEGER
)
    """

    make_table(address_df, schema, table_name,db_path)

def make_address_index(db_path: str) -> None:
    """Makes an index of the qAddress column of the address table."""
    query = """
    CREATE INDEX "qAddress_index"
    ON "addresses" ("qAddress")
    """

    with sqlite3.connect(db_path) as con:

        cur = con.cursor()
        result = cur.execute(query)

def make_db(
    address_df: pd.DataFrame, species_df: pd.DataFrame, db_path: str, address_table_func
) -> None:
    make_species_table(species_df, db_path)
    address_table_func(address_df, db_path)


def make_simple_db(
    address_df: pd.DataFrame, species_df: pd.DataFrame, db_path: str
) -> None:
    pass


def main():
    addresses: pd.DataFrame
    # load addresses and species as df
    addresses = load_original_data(TREE_LIST_PATH)
    species = load_original_data(MAPPED_SPECIES_PATH)

    # throw warning if a species in addresses is not in mapped species
    if species_difference(addresses.qSpecies.tolist(), species.qSpecies.tolist()):
        logging.warning(
            f"{species_difference} is in the tree list but not in the mapped species"
        )

    # select qAddress and qSpecies
    addresses = addresses.loc[:, ["qAddress", "qSpecies"]].astype(
        {"qAddress": "string"}
    )

    # create dict mapping qSpecies to species key and replace qSpecies with the key
    species_dict = (
        species.reset_index()
        .set_index("qSpecies")
        .drop("urlPath", axis=1)
        .to_dict()["index"]
    )
    addresses = addresses.replace({"qSpecies": species_dict})

    # clean up addresses
    addresses = addresses.astype({"qSpecies": "uint16"})

    addresses.to_csv('table_making.csv')

    make_species_table(species, DB_PATH)
    make_address_table(addresses, DB_PATH)
    # make_address_index(DB_PATH)


if __name__ == "__main__":
    main()
    print(get_db_tables(DB_PATH))
    print(get_db_indicies(DB_PATH))
