from timeit import timeit
import os
import sys

# adds python module to path
path_to_append = os.path.join('.', 'src')
sys.path.append(path_to_append)
from url_finder import url_finder
from SF_Tree_Identifier import Address

def test_get_selec_tree_url_path(number: int = 100):
    search_term = url_finder.Specie(formatted_name='Gleditsia triacanthos "Sunburst" :: Sunburst Honey Locust')
    possible_ids = url_finder.query_selec_tree(search_term.full_name)
    print(timeit(lambda: (url_finder.find_closest_match(search_term, possible_ids, 'full_name')), number=number) / number)

def test_load_street_types(number: int = 1000):
    time = timeit(lambda: (Address.load_street_type_abbreviations()), number=number) / number
    print()

def test_street_name_matching(number: int = 1000):
    street_names = Address.load_street_names()
    address = Address.Address('1468 vaelncia st')
    time = timeit(lambda: (Address.match_closest_street_name(address, street_names)), number=number) / number
    print(f'Closest match avg. time: {time}s')

if __name__ == "__main__":
    test_street_name_matching()
    test_load_street_types()