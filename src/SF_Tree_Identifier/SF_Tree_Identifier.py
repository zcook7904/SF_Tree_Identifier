import logging
import sqlite3
import os
from timeit import timeit
import Address

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

    if check_nearby:
        # tests street number, street number + 2, street_number - 2 (i.e. 1468,  1470, 1464)
        steps = [-4, 2, 0]
    else:
        # only tests given address street number
        steps = [0]

    keys = None
    while keys is None and len(steps) > 0:
        query_address.street_number = int(query_address.street_number) + steps.pop()
        keys = get_species_keys(query_address)

    if keys is None:
        raise Exception(f'Can\'t find any trees near entered street number')

    if len(steps) < 2:
        logging.warning(f'Couldn\'t find trees at given address, some found at {query_address.street_number} though')

    qSpecies = []
    urlPaths = []
    species = []
    for key in keys:
        qSpecie, urlPath = get_species(key)
        specie_dict = {qSpecie: urlPath}
        species.append(specie_dict)

    return species, query_address.street_address.title()

def format_output(qSpecies: list, query_address):
    print(dict(Counter(qSpecies)))

if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    time = timeit(lambda: (main('1470 Valenci St')), number=100) / 100
    print(f'Time: {time}s')
