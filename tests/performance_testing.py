from timeit import timeit

# adds python module to path
path_to_append = os.path.join('.', 'src')
sys.path.append(path_to_append)
from url_finder import url_finder

def test_find_closest_match():
    search_term = url_finder.get_Species_from_qSpecies('Gleditsia triacanthos "Sunburst" :: Sunburst Honey Locust')
