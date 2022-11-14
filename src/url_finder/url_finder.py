import os.path
import logging
import requests
import time
import pandas as pd
import numpy as np
import random

logging.basicConfig(filename='url_finder.log', filemode='w', level=logging.WARNING)

class SelecTreeResultNotFoundError(Exception):
    """Raised when a SelecTree result isn't found."""
    pass

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
    payload = {'searchTerm': species_name, 'activePage': 1, 'resultsPerPage': 10, 'sort': 1}
    r = requests.get(url, params=payload, timeout=1)

    if not hasattr(selec_tree_number, '_attempt'):
        selec_tree_number._attempt = 1

    def check_returned_id(result: dict, search_term: str) -> True:
        """Checks if the returned results contains the search term."""
        if result['common'].lower().contains(search_term.lower()):
            return True
        elif result['name_unformatted'].lower().contains(search_term.lower()):
            return True

        return False


    def get_id_from_request(json_obj) -> int:

        num_results = len(json_obj['pageResults'])

        if num_results == 0:
            raise SelecTreeResultNotFoundError

        elif num_results == 1:
            first_result = json_obj['pageResults'][0]
            id = first_result['tree_id']
            returned_name = first_result['common']
            logging.debug(f'Result for {species_name}: {returned_name}')

            return id

        elif num_results > 1:
            # will loop through results with check_returned_id(result, species_name) and if of first true
            # need to test check_returned_id first

            first_result = json_obj['pageResults'][0]
            id = first_result['tree_id']
            returned_name = first_result['common']
            logging.warning(f'Multiple results returned for {species_name}; returned result was {id=}: {returned_name}')
            return id

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

def assign_url_paths(species: pd.Series, time_buffer: bool = True, show_progress: bool = False) -> pd.DataFrame:
    """Takes the species series as input and returns a dataframe containing the original series
    and the url path number (key) appended as a coloumn"""

    def map_url(scientific_name, common_name, time_buffer: bool = True):
        #time buffer to not abuse Selec Tree or be banned
        if time_buffer:
            wait_time = random.randint(1, 3)
            time.sleep(wait_time * .5)


        if not pd.isna(common_name):
            try:
                id = selec_tree_number(common_name)
                return id
            except SelecTreeResultNotFoundError:
                pass

        else:
            #removing leftover seperator pandas leaves if no common name is included in the species
            scientific_name = scientific_name.replace(' ::', '')

        id = selec_tree_number(scientific_name)
        return id


    split_species_names = species.str.split(' :: ', expand=True).rename(columns={0: 'ScientificName', 1: 'CommonName'})
    num_species = len(species)
    urlPaths = pd.Series(np.zeros(num_species, dtype='uint16'))

    for row in split_species_names.itertuples():
        try:
            urlPaths.loc[row.Index] = map_url(row.ScientificName,row.CommonName, time_buffer)

        except ConnectionError as err:
            logging.error(f'Connection error while mapping {row}: {err}')
            urlPaths.loc[row.Index] = 0

        except SelecTreeResultNotFoundError:
            logging.error(f'Selec Tree result not found while mapping {row}')
            urlPaths.loc[row.Index] = 0

        except Exception as err:
            logging.error(f'Exception while mapping {row}: {err=}')
            urlPaths.loc[row.Index] = 0

        if show_progress:
            print(f'{row.Index + 1}/{num_species}', end='\r')

            if row.Index + 1 == num_species:
                #new line to overwrite carriage
                print()

    mapped_series = pd.concat([species, urlPaths], axis=1).rename({ 0: 'urlPath'}, axis=1)

    return mapped_series

if __name__ == '__main__':
    start_time = time.time()
    species_path = os.path.join('src', 'SF_Tree_Identifier', 'data', 'Species.csv')
    species_series = pd.read_csv(species_path, index_col=0).iloc[:10, 0]
    species_df = assign_url_paths(species_series, show_progress=True)
    #species_df.to_csv('species_urls.csv')

    time_taken = time.time() - start_time
    mins = int(time_taken // 60)
    seconds = time_taken % 60
    print(f'Done! Time taken: {mins}min {seconds:.0f}s')


