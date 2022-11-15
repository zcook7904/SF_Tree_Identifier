import os.path
import logging
import requests
import time
import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
import random
import argparse
from collections import namedtuple

logging.basicConfig(filename='url_finder.log', filemode='w', level=logging.WARNING)

class SelecTreeResultNotFoundError(Exception):
    """Raised when a SelecTree result isn't found."""
    pass

Specie = namedtuple('Specie', 'scientific_name common_name')


#TODO implement argparse

def wiki_exists(species_name: str) -> bool:
    url = f'https://en.wikipedia.org/wiki/{species_name}'
    r = requests.get(url)
    if r.status_code == 200:
        return True

    return False

def selec_tree_number(specie: Specie, max_attempts: int = 2, results_per_page: int = 10) -> int:
    """Returns the SelecTree URL path ID for the given species name. Essentially returns the first result from the
    SelecTree Seach API. Returns 0 if no search result is found."""

    if specie.common_name:
        search_term = f'{specie.scientific_name} {specie.common_name}'
    else:
        search_term = specie.scientific_name

    url = 'https://selectree.calpoly.edu/api/search-by-name-multiresult'
    payload = {'searchTerm': search_term, 'activePage': 1, 'resultsPerPage': results_per_page, 'sort': 1}
    r = requests.get(url, params=payload, timeout=1)

    if not hasattr(selec_tree_number, '_attempt'):
        selec_tree_number._attempt = 1


    def get_id_from_request(json_obj: dict, specie: Specie) -> int:

        num_results = len(json_obj['pageResults'])

        if num_results == 0:
            raise SelecTreeResultNotFoundError

        elif num_results == 1:
            first_result = json_obj['pageResults'][0]
            id = first_result['tree_id']
            returned_name = first_result['common']
            logging.debug(f'Result for {specie}: {returned_name}')

            return id

        elif num_results > 1:
            # will fuzz match results to scientific name and common name
            # return id with highest ratio

            return id

    if r.status_code == 200:
        selec_tree_number._attempt = 1
        return get_id_from_request(r.json())

    elif selec_tree_number._attempt < max_attempts:
        selec_tree_number._attempt += 1
        time.sleep(.5)
        selec_tree_number(species_name, max_attempts=max_attempts)

    else:
        selec_tree_number._attempt = 1
        raise ConnectionError(f'Bad status code: {r.status_code}')

def assign_url_paths(species: pd.Series, time_buffer: bool = True, show_progress: bool = False) -> pd.DataFrame:
    """Takes the species series as input and returns a dataframe containing the original series
    and the url path number (key) appended as a coloumn"""

    def split_species_name(species_name: str) -> (str, str | None):
        """"Returns the scientific and common name from the species species csv. If no common name exists, """

    def map_url(species_name, time_buffer: bool = True):
        #time buffer to not abuse Selec Tree or be banned
        if time_buffer:
            wait_time = random.randint(1, 3)
            time.sleep(wait_time * .5)

        id = selec_tree_number(species_name)
        return id

    num_species = len(species)
    urlPaths = pd.Series(np.zeros(num_species, dtype='uint16'))

    for i, specie in species.items():
        try:

            urlPaths.loc[i] = map_url(specie, time_buffer)

        except ConnectionError as err:
            logging.error(f'Connection error while mapping {row}: {err}')
            urlPaths.loc[i] = 0

        except SelecTreeResultNotFoundError:
            logging.error(f'Selec Tree result not found while mapping {row}')
            urlPaths.loc[i] = 0

        except Exception as err:
            logging.error(f'Exception while mapping {row}: {err=}')
            urlPaths.loc[i] = 0

        if show_progress:
            print(f'{i + 1}/{num_species}', end='\r')

            if i + 1 == num_species:
                #new line to overwrite carriage
                print()

    mapped_series = pd.concat([species, urlPaths], axis=1).rename({ 0: 'urlPath'}, axis=1)

    return mapped_series

if __name__ == '__main__':
    start_time = time.time()
    species_path = os.path.join('src', 'SF_Tree_Identifier', 'data', 'Species.csv')
    species_series = pd.read_csv(species_path, index_col=0).iloc[:, 0]
    species_df = assign_url_paths(species_series, show_progress=True)
    species_df.to_csv('species_urls.csv')

    #calculate number missing vs complete
    num_missing = species_df.loc[species_df.urlPath == 0].size
    total_species, _ = species_df.shape

    #calculate time taken
    time_taken = time.time() - start_time
    mins = int(time_taken // 60)
    seconds = time_taken % 60

    # print results
    print(f'Done! Time taken: {mins}min {seconds:.0f}s')
    print(f'Number of species missing paths: {num_missing}/{total_species}')


