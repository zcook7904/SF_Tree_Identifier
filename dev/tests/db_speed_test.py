import sqlite3
import os
from timeit import timeit
import sys

os.chdir(os.path.dirname(__file__))
IMPORT_PATH = os.path.join('..', '..', 'src')
sys.path.append(IMPORT_PATH)
DB_PATH = os.path.join("..", "test_db.db")

from src.SF_Tree_Identifier import identify_trees
address = '1470 valencia st'
number = 100

identify_trees.DB_LOCATION = DB_PATH

result = identify_trees.get_address_species_keys(address)
time = timeit(lambda: identify_trees.get_address_species_keys(address), number=number) / number  # s
print(f'No index - time: {time: .5f}s')


def new_create_address_query(street_address: str) -> str:
    """Creates the sql query to retrieve the qSpecies keys for a specfic address. Returns the query as a string."""
    query = f"""
        SELECT qSpecies
        FROM addresses
        INDEXED BY "qAddress_index"
        WHERE qAddress = '{street_address}'"""
    return query

identify_trees.create_address_query = new_create_address_query


result = identify_trees.get_address_species_keys(address)
time = timeit(lambda: identify_trees.get_address_species_keys(address), number=number) / number  # s
print(result)
print(f'Index - time: {time: .5f}s')
print(result)

