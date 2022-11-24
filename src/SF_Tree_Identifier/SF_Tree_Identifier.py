import logging
import sqlite3
import os
from timeit import timeit
from collections import namedtuple
from . import Address
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_LOCATION = os.path.join(DATA_DIR, 'SF_Trees.db')

def create_address_query(address: Address) -> str:
    query = f"""
        SELECT qSpecies
        FROM addresses
        WHERE qAddress = '{address.street_address}'"""
    return query

def create_species_query(key) -> str:
    query = f"""
        SELECT qSpecies, urlPath
        FROM species
        WHERE "index" = {key}"""
    return query

def query_db(query: str):
    con = sqlite3.connect(DB_LOCATION)
    cur = con.cursor()
    result = cur.execute(query)

    if result:
        result = result.fetchall()

    con.close()
    return result
def get_species_keys(address: Address, check_nearby: bool = True) -> str|None:
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
        result = result[0] # should only be one species per key
        qSpecies = result[0]
        urlPaths = str(result[1])
        return qSpecies, urlPaths

    else:
        return None

def main(user_input: str, check_nearby: bool = True) -> tuple:
    try:
        query_address = Address.get_Address_for_query(user_input)
    except Address.NoCloseMatchError:
        raise Exception('Address not found in San Francisco')
    except Address.AddressError as err:
        raise Exception('Invalid address entered, ensure proper street address is given.')


    address_key = namedtuple('AddressKeys', ['address', 'key'])
    address_keys = []
    keys = None

    keys = get_species_keys(query_address)

    if not keys is None:
        for key in keys:
            address_keys.append(address_key(query_address.street_address, key))

    if keys is None and check_nearby:
        logging.warning(f'Couldn\'t find trees at given address, looking nearby...')
        steps = [-4, 2]

        while len(steps) > 0:
            query_address.street_number = int(query_address.street_number) + steps.pop()
            keys = get_species_keys(query_address)
            if not keys is None:
                for key in keys:
                    address_keys.append(address_key(query_address.street_address, key))

    if len(address_keys) == 0:
        raise Exception(f"Can't find any trees near entered street number")

    results = pd.DataFrame(columns=['qSpecies', 'urlPath', 'queried_address'], index=[i for i in range(len(address_keys))])

    for i, item in enumerate(address_keys):
        qSpecie, urlPath = get_species(item.key)
        results.loc[i] = {'qSpecies': qSpecie, 'urlPath': urlPath, 'queried_address': item.address.title()}

    return results

def format_output(results: pd.DataFrame):
    results.groupby()


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    time = timeit(lambda: (main('1468 Valenci St')), number=100) / 100
    print(f'Time: {time}s')

# if __name__ == "__main__":
#     main('900 Brotherhood Way').to_csv('brotherhood.csv')
