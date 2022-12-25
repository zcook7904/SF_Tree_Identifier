import pandas as pd
import os
import logging
import time
import pickle

os.chdir(os.path.dirname(__file__))
TREE_LIST_PATH = os.path.join("..", "Cleaned_Street_Tree_List.csv")
MAPPED_SPECIES_PATH = os.path.join("..", "mapped_species.csv")
ADDRESS_PATH = os.path.join("..", "SF_trees.pkl")
SPECIES_PATH = os.path.join("..", "species_dict.pkl")


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

def make_species_dict(species: pd.DataFrame, species_path: str) -> None:
    """Creates and saves a dictionary containing {species_key: {'qSpecies': [qSpecies: str], 'urlPath': [urlPath: int}}"""
    species_dict = species.to_dict('index')
    with open(species_path, 'wb') as fp:
        pickle.dump(species_dict, fp)

def make_address_dict(addresses: pd.DataFrame, address_path: str) -> None:
    """Creates and saves a dictionary containing {street_name: {street_number: [species_key1: int, species_key2, ...]}"""
    street_names = addresses.street_name.unique().tolist()

    tree_dict = dict()

    for street_name in street_names:
        street_trees = addresses.loc[addresses.street_name == street_name][['street_number', 'qSpecies']]
        tree_dict.update({street_name: {}})

        for row in street_trees.itertuples():

            if row.street_number in tree_dict[street_name]:
                tree_dict[street_name][row.street_number].append(row.qSpecies)
            else:
                tree_dict[street_name].update({row.street_number: [row.qSpecies]})


    with open(address_path, 'wb') as fp:
        pickle.dump(tree_dict, fp)

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
    addresses[['street_number', 'street_name']] = addresses.qAddress.str.split(' ', n=1, expand=True)
    addresses = addresses[['street_number', 'street_name', 'qSpecies']]
    addresses = addresses.dropna().astype({'street_number': 'int64'}).sort_values(['street_name', 'street_number'])

    addresses.to_csv('table_making.csv')

    make_species_dict(species, SPECIES_PATH)
    make_address_dict(addresses, ADDRESS_PATH)
    # make_address_index(DB_PATH)


if __name__ == "__main__":
    start = time.time()
    main()
    tot_time = time.time() - start
    print(f'Total time: {tot_time: .2f}')
