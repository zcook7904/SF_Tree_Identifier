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

"""Search results from selec tree API are in the form of:
{
  "totalResults": 82,
  "pageResults": [
    {
      "tree_id": 39,
      "family": "Sapindaceae",
      "common": "TRIDENT MAPLE",
      "name_concat": "<em>Acer</em> <em>buergerianum</em>",
      "name_unformatted": "Acer buergerianum",
      "link": "/images/0000/39/original/acer-buergerianum-acer-buergerianum-ro.jpg",
      "sequence": 1,
      "low_zone": 1,
      "height_high": 25
    },
  "sort": 1,
  "resultsPerPage": "30",
  "activePage": "1"
}
"""

global score_count
score_count = [0, 0] #total score, number of times score is calculated

logging.basicConfig(filename='url_finder.log', filemode='w', level=logging.WARNING)

class SelecTreeResultNotFoundError(Exception):
    """Raised when a SelecTree result isn't found."""
    pass

Specie = namedtuple('Specie', 'scientific_name common_name')

def get_Specie_from_qSpecies(species_name: str) -> Specie:
    """"Returns the scientific and common name from the species.csv qSpecies. If no common name exists, the common
    name atttribute will be assigned None."""
    if species_name.endswith(' ::'):
        scientific_name = species_name.replace(' ::', '')
        return Specie(scientific_name, None)
    else:
        scientific_name, common_name = species_name.split(' :: ')
        return Specie(scientific_name, common_name)



def find_closest_match(specie: Specie, search_results: list, weight: float = 1) -> int:
    """Takes a Specie and search results from Selec Tree and returns the index of the
    closest matching result to the specie. Optional kwarg 'weight' applies a multiplier to the scientific name score"""
    scores = np.zeros(len(search_results))

    for i, result in enumerate(search_results):
        if specie.common_name.lower() == result['common'].lower() or \
                specie.scientific_name.lower() == result["name_unformatted"].lower():
            logging.warning(f'Perfect match: {specie}: {result["name_unformatted"]}')
            return i

        else:
            common_name_score = fuzz.token_sort_ratio(specie.common_name.lower(), result['common'].lower())
            scientific_name_score = fuzz.token_sort_ratio(specie.scientific_name.lower(),
                                                         result['name_unformatted'].lower())
            scores[i] = common_name_score + scientific_name_score * weight


    score_count[0] += scores.max()
    score_count[1] += 1

    closest_match_index = np.argmax(scores)
    logging.warning(f'Multi result for {specie}. '
                 f'Highest scoring result: {search_results[closest_match_index]["name_unformatted"]} :: {search_results[closest_match_index]["common"]}'
                 f'Score: {scores.max()}')
    return closest_match_index


#TODO implement argparse

#Want to separate getting search results and processing results for testing purposes
def get_selec_tree_search_results(search_term: str) -> dict:
    pass

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


    def get_id_from_request(search_results: list, specie: Specie) -> int:

        num_results = len(search_results)

        if num_results == 0:
            # need to perform search again with specie.scientific_name and specie.common_name
            raise SelecTreeResultNotFoundError

        elif num_results == 1:
            first_result = search_results[0]
            id = first_result['tree_id']
            returned_name = first_result['common']
            logging.debug(f'Result for {specie}: {returned_name}')

            return id

        elif num_results > 1:
            closest_match = search_results[find_closest_match(specie, search_results)]
            return closest_match['tree_id']

    if r.status_code == 200:
        search_results = r.json()['pageResults']
        selec_tree_number._attempt = 1
        return get_id_from_request(search_results, specie)
# functions should be flipper. This function will return search_results to get_id or raise error
    elif selec_tree_number._attempt < max_attempts:
        selec_tree_number._attempt += 1
        time.sleep(.5)
        selec_tree_number(specie, max_attempts=max_attempts)

    else:
        selec_tree_number._attempt = 1
        raise ConnectionError(f'Bad status code: {r.status_code}')

def assign_url_paths(species: pd.Series, time_buffer: bool = True, show_progress: bool = False) -> pd.DataFrame:
    """Takes the species series as input and returns a dataframe containing the original series
    and the url path number (key) appended as a coloumn"""


    def map_url(species_name, time_buffer: bool = True) -> int:
        #time buffer to not abuse Selec Tree or be banned
        if time_buffer:
            wait_time = random.randint(1, 3)
            time.sleep(wait_time * .5)

        id = selec_tree_number(species_name)
        return id

    num_species = len(species)
    urlPaths = pd.Series(np.zeros(num_species, dtype='uint16'))

    for i, specie_name in species.items():
        try:
            specie = get_Specie_from_qSpecies(specie_name)
            urlPaths.loc[i] = map_url(specie, time_buffer)

        except ConnectionError as err:
            logging.error(f'Connection error while mapping {species[i]}: {err}')
            urlPaths.loc[i] = 0

        except SelecTreeResultNotFoundError:
            logging.error(f'Selec Tree result not found while mapping {species[i]}')
            urlPaths.loc[i] = 0

        except Exception as err:
            logging.error(f'Exception while mapping {species[i]}: {err=}')
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
    if score_count[1] > 0:
        print(f'Multi result occured {score_count[1]} times, average score was {score_count[0] / score_count[1]: .0f}')

