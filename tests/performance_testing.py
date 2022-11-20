from timeit import timeit
import os
import sys

# adds python module to path
path_to_append = os.path.join('.', 'src')
sys.path.append(path_to_append)
from url_finder import url_finder

def test_get_selec_tree_url_path(number: int = 100):
    search_term = url_finder.Specie(formatted_name='Gleditsia triacanthos "Sunburst" :: Sunburst Honey Locust')
    possible_ids = url_finder.query_selec_tree(search_term.full_name)
    print(timeit(lambda: (url_finder.find_closest_match(search_term, possible_ids, 'full_name')), number=number) / number)


if __name__ == "__main__":
    test_get_selec_tree_url_path(number=10000)