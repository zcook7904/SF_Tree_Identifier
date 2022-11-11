import requests
import time
import pandas

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



if __name__ == '__main__':
    pass


