import sqlite3
import pandas as pd
import os
import logging

os.chdir(os.path.dirname(__file__))
TREE_LIST_PATH = os.path.join("..", "Cleaned_Street_Tree_List.csv")
MAPPED_SPECIES_PATH = os.path.join("..", "mapped_species.csv")
DB_PATH = os.path.join('..', 'test_db.db')

def load_original_data(path: str) -> pd.DataFrame:
    """Loads the original data csv and returns a pandas dataframe of the csv file."""
    try:
        return pd.read_csv(path, index_col=0)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Cannot find {os.path.abspath(path)}"
        )

def species_difference(species_list_1: list, species_list_2: list) -> set:
    """Determines if a species from list 1 is not in list 2. Returns the set of the difference"""
    address_species_set = set(species_list_1)
    mapped_species_set = set(species_list_2)
    return address_species_set.difference(mapped_species_set)

def make_species_table(species_df: pd.DataFrame, db_path: str) -> None:
    with sqlite3.connect(db_path) as con:

        cur = con.cursor()
        query = """
        CREATE TABLE "species" (
        "index" INTEGER PRIMARY KEY,
          "qSpecies" TEXT,
          "urlPath" INTEGER
        )

        """
        result = cur.execute(query)

        species_df.to_sql('species', con, if_exists='append')


def make_db(address_df: pd.DataFrame, species_df: pd.DataFrame, db_path: str, address_table_func) -> None:
    make_species_table(species_df, db_path)
    address_table_func(address_df, db_path)

def make_simple_db(address_df: pd.DataFrame, species_df: pd.DataFrame, db_path: str) -> None:
    pass


def main():
    addresses: pd.DataFrame
    # load addresses and species as df
    addresses = load_original_data(TREE_LIST_PATH)
    species = load_original_data(MAPPED_SPECIES_PATH)

    # throw warning if a species in addresses is not in mapped species
    if species_difference(addresses.qSpecies.tolist(), species.qSpecies.tolist()):
        logging.warning(f'{species_difference} is in the tree list but not in the mapped species')

    # select qAddress and qSpecies
    addresses = addresses.loc[:, ['qAddress', 'qSpecies']].astype(
        {'qAddress': 'string'})

    # create dict mapping qSpecies to species key and replace qSpecies with the key
    species_dict = species.reset_index().set_index('qSpecies').drop('urlPath', axis=1).to_dict()['index']
    addresses = addresses.replace({'qSpecies': species_dict})

    # clean up addresses
    addresses = addresses.astype({'qSpecies': 'uint16'})

    #make_species_table(species, DB_PATH)


if __name__ == "__main__":
    main()
