import os.path

import requests
import time
import pandas as pd
import numpy as np
import random

def wiki_exists(species_name: str) -> bool:
    url = f'https://en.wikipedia.org/wiki/{species_name}'
    r = requests.get(url)
    if r.status_code == 200:
        return True

    return False

def selec_tree_number(species_name: str, max_attempts: int = 2) -> int:
    """Returns the SelecTree URL path ID for the given species name. Essentially returns the first result from the
    SelecTree Seach API. Raises IndexError if the search returns no trees."""

    url = 'https://selectree.calpoly.edu/api/search-by-name-multiresult'
    payload = {'searchTerm': species_name, 'activePage': 1, 'resultsPerPage': 1, 'sort': 1}
    r = requests.get(url, params=payload, timeout=1)

    if not hasattr(selec_tree_number, '_attempt'):
        selec_tree_number._attempt = 1

    def get_id_from_request(json_obj) -> int:
        try:
            id = json_obj['pageResults'][0]['tree_id']
            return id

        except IndexError:
            raise IndexError(f'No SelecTree Results found for {species_name}')

    if r.status_code == 200:
        selec_tree_number._attempt = 1
        return get_id_from_request(r.json())

    elif selec_tree_number._attempt < max_attempts:
        selec_tree_number._attempt += 1
        time.sleep(.5)
        selec_tree_number(species_name, max_attempts=max_attempts)

    else:
        # will change this to raise
        selec_tree_number._attempt = 1
        raise ConnectionError(f'Bad status code: {r.status_code}')

def assign_url_paths(species: pd.Series, time_buffer: bool = False) -> pd.DataFrame:
    def map_url(val: str, time_buffer: bool):
        #time buffer to not abuse Selec Tree or be banned
        if time_buffer:
            wait_time = random.randint(1, 3)
            time.sleep(wait_time)

        scientific_name, common_name = val.split(' :: ')

        try:
            id = selec_tree_number(common_name)
            return id


        # when no results are found for the common name, scientific name used
        except IndexError:
            try:
                return selec_tree_number(scientific_name)

            # if no results for scientific name, nan is returned
            except IndexError:
                pass

            #connection error is returned and error is printed
            except  ConnectionError as e:
                print(f'Connection error {e}')
        except  ConnectionError as e:
            print(f'Connection error {e}')


        return 0

    species_list = species.astype('string').to_list()
    urlPaths = pd.Series(np.zeros(len(species), dtype='uint16'))

    for i, specie in enumerate(species_list):
        urlPaths.loc[i] = map_url(specie, time_buffer)

    mapped_series = pd.concat([species, urlPaths], axis=1).rename({ 0: 'urlPath'}, axis=1)

    return mapped_series

if __name__ == '__main__':
    species_path = os.path.join('src', 'SF_Tree_Identifier', 'data', 'Species.csv')
    species_series = pd.read_csv(species_path, index_col=0).iloc[:, 0]
    species_df = assign_url_paths(species_series)
    species_df.to_csv('test.csv')


