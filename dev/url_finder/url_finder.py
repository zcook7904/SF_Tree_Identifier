import os.path
import logging
import requests
from requests.exceptions import HTTPError
import time
from dataclasses import dataclass
import pandas as pd
import numpy as np
from thefuzz import fuzz
import random
import argparse

# TODO add in X addresses

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
score_count = [0, 0]  # total score, number of times score is calculated

FILENAME = "mapped_species"
logging.basicConfig(filename=f"{FILENAME}.log", filemode="w", level=logging.WARNING)


class SelecTreeResultNotFoundError(Exception):
    """Raised when a SelecTree result isn't found."""

    pass


@dataclass
class Specie:
    scientific_name: str
    common_name: str
    tree_id: int

    def __init__(
        self,
        scientific_name=None,
        common_name=None,
        formatted_name=None,
        pageResult=None,
        tree_id=None,
    ):
        if (
            (common_name is None or scientific_name is None)
            ^ (formatted_name is None)
            ^ (pageResult is None)
        ):
            raise ValueError("Too many args passed to init Specie")

        elif pageResult:
            (
                self.tree_id,
                self.scientific_name,
                self.common_name,
            ) = self._set_Specie_from_pageResult(pageResult)

        elif formatted_name:
            (
                self.scientific_name,
                self.common_name,
            ) = self._set_Specie_from_formatted_name(formatted_name)

        else:
            self.scientific_name = scientific_name
            self.common_name = common_name

        if not hasattr(self, "tree_id"):
            self.tree_id = tree_id

    @property
    def formatted_name(self) -> str:
        if self.common_name and self.scientific_name:
            return f"{self.scientific_name} :: {self.common_name}"

        elif self.scientific_name:
            return f"{self.scientific_name} ::"

        elif self.common_name:
            return f":: {self.common_name}"

        else:
            raise UserWarning("No common or scientific name set for Specie")
            return None

    @property
    def full_name(self):
        if self.common_name and self.scientific_name:
            return f"{self.scientific_name} {self.common_name}"

        elif self.scientific_name:
            return f"{self.scientific_name}"

        elif self.common_name:
            return f"{self.common_name}"

        else:
            raise UserWarning(f"No common or scientific name set for {self}")
            return None

    def _set_Specie_from_formatted_name(self, species_name: str):
        """ "Returns the scientific and common name from the species.csv qSpecies. If no common name exists, the common
        name atttribute will be assigned None."""
        if species_name.endswith(" ::"):
            scientific_name = species_name.replace(" ::", "")
            return scientific_name, None
        else:
            scientific_name, common_name = species_name.split(" :: ")
            return scientific_name, common_name

    def _set_Specie_from_pageResult(self, pageResult: dict):
        """Creates a new Specie object from a selec tree pageResult dict passed as Specie(pageResult={pageResult dict}.
        Will assign tree_id from pageResult to new Specie object."""
        tree_id = pageResult["tree_id"]
        common_name = pageResult["common"]
        scientific_name = (
            pageResult["name_unformatted"].replace("<em>", "").replace("</em>", "")
        )
        return tree_id, scientific_name, common_name


def _get_match_scores(
    specie: Specie, search_results: list[Specie], property: str
) -> np.array:
    """Base function for assigning matching scores between Specie specie to list of other Species.
    The variable 'property' determines which (string) property of the Specis is being matched between.
    Returns a numpy array of the scores with the same indices as the original search_result list passed to the function."""
    scores = np.zeros(len(search_results))
    for i, result in enumerate(search_results):
        score = fuzz.partial_token_sort_ratio(
            getattr(specie, property).lower(), getattr(result, property).lower()
        )
        scores[i] = score

    return scores


def get_common_name_match_scores(specie: Specie, search_results: list[Specie]):
    """Implements _get_match_scores() for the common_name Species property"""
    if specie.common_name:
        return _get_match_scores(specie, search_results, "common_name")
    else:
        raise ValueError(f"No common name assigned to {specie}")


def get_scientific_name_match_scores(specie: Specie, search_results: list[Specie]):
    """Implements _get_match_scores() for the common_name Species property"""
    if specie.scientific_name:
        return _get_match_scores(specie, search_results, "scientific_name")

    else:
        raise ValueError(f"No scientific name assigned to {specie}")


def query_selec_tree(search_term: str, results_per_page: int = 10) -> list:
    """Queries selec tree for the passed search term. Returns the results as a list of Species objects."""
    url = "https://selectree.calpoly.edu/api/search-by-name-multiresult"
    payload = {
        "searchTerm": search_term,
        "activePage": 1,
        "resultsPerPage": results_per_page,
        "sort": 1,
    }
    r = requests.get(url, params=payload, timeout=2)

    if r.status_code == 200:
        search_results = r.json()["pageResults"]

        search_result_species = list()
        for result in search_results:
            search_result_species.append(Specie(pageResult=result))

        return search_result_species

    try:
        r.raise_for_status()

    except HTTPError as err:
        raise HTTPError(f"Error for {search_term}: {err}")

    except Exception as err:
        raise ConnectionError(f"Connection error (non-HTTP) for {search_term}: {err}")


def find_closest_match(
    specie: Specie,
    possible_ids: list[Specie],
    key: str,
    weight: int,
    minimum_score: int = 55,
):
    num_results = len(possible_ids)

    if num_results == 1:
        result_specie = possible_ids[0]
        logging.warning(f"Result for {specie}: {result_specie.formatted_name}")

        return result_specie.tree_id

    # full_name vs common_name vs scientific_name logic
    if key == "full_name":
        scientific_name_scores = get_scientific_name_match_scores(specie, possible_ids)
        if max(scientific_name_scores) == 100:  # perfect match
            location = np.where(scientific_name_scores == 100)[0][0]
            logging.warning(
                f"The scientific name was a perfect match for {specie}: {possible_ids[location]}"
            )
            return possible_ids[location].tree_id

        common_name_scores = get_common_name_match_scores(specie, possible_ids)
        if max(common_name_scores) == 100:  # perfect match
            location = np.where(common_name_scores == 100)[0][0]
            logging.warning(
                f"The common name was a perfect match for {specie}: {possible_ids[location]}"
            )
            return possible_ids[location].tree_id

        # weighted average of two scores
        total_scores = (scientific_name_scores * weight + common_name_scores) / (
            weight + 1
        )
        if max(total_scores) > minimum_score:
            location = np.where(total_scores == total_scores.max())[0][0]
            logging.warning(
                f"Search results using the {key} of {specie} returned {possible_ids[location]}. "
                f"Weighted score = {total_scores.max()}"
            )
            return possible_ids[location].tree_id

    elif key == "scientific_name":
        scientific_name_scores = get_scientific_name_match_scores(specie, possible_ids)
        if max(scientific_name_scores) == 100:  # perfect match
            location = np.where(scientific_name_scores == 100)[0][0]
            return possible_ids[location].tree_id

        if max(scientific_name_scores) > minimum_score:
            location = np.where(scientific_name_scores == scientific_name_scores.max())[
                0
            ][0]
            logging.warning(
                f"Search results using the {key} of {specie} returned {possible_ids[location]}. "
                f"Score = {scientific_name_scores.max()}"
            )
            return possible_ids[location].tree_id

    elif key == "common_name":
        common_name_scores = get_common_name_match_scores(specie, possible_ids)
        if max(common_name_scores) == 100:  # perfect match
            location = np.where(common_name_scores == 100)[0][0]
            logging.warning(
                f"The common name was a perfect match for {specie}: {possible_ids[location]}"
            )
            return possible_ids[location].tree_id

        if max(common_name_scores) > minimum_score:
            location = np.where(common_name_scores == common_name_scores.max())[0][0]
            logging.warning(
                f"Search results using the {key} of {specie} returned {possible_ids[location]}. "
                f"Score = {common_name_scores.max()}"
            )
            return possible_ids[location].tree_id

    else:
        raise Error("get_selec_tree_url_path key not found in matching statements")

    # if no id is returned
    logging.error(f"No strong match for {specie}")
    return 0


def get_selec_tree_url_path(specie: Specie, weight: float = 1) -> int:
    """Takes a tree specie Specie as argument and returns the url path from selec tree to the closest matching page."""
    if not specie.common_name:
        search_terms = {"scientific_name": specie.scientific_name}

    else:
        search_terms = {
            "full_name": specie.full_name,
            "scientific_name": specie.scientific_name,
            "common_name": specie.common_name,
        }

    num_results = 0

    for key in search_terms:
        search_term = search_terms[key]
        possible_ids = query_selec_tree(search_term)
        num_results = len(possible_ids)
        if num_results > 0:
            break
    else:
        raise SelecTreeResultNotFoundError

    return find_closest_match(specie, possible_ids, key, weight)


def assign_url_paths(
    species: pd.Series,
    time_buffer: bool = True,
    show_progress: bool = False,
    weight: float = 1.2,
) -> pd.DataFrame:
    """Takes the species series as input and returns a dataframe containing the original series
    and the url path number (key) appended as a coloumn"""

    def map_url(species_name, time_buffer: bool = True) -> int:
        # time buffer to not abuse Selec Tree or be banned
        if time_buffer:
            wait_time = random.randint(1, 3) * 2
            time.sleep(wait_time)

        id = get_selec_tree_url_path(species_name, weight=1.2)
        return id

    num_species = len(species)
    urlPaths = pd.Series(np.zeros(num_species, dtype="uint16"))

    for i, specie_name in species.items():
        try:
            specie = Specie(formatted_name=specie_name)
            urlPaths.loc[i] = map_url(specie, time_buffer)

        except HTTPError as err:
            logging.error(f"HTTP error while mapping {species[i]}: {err}")
            urlPaths.loc[i] = 0

        except ConnectionError as err:
            logging.error(f"Connection error while mapping {species[i]}: {err}")
            urlPaths.loc[i] = 0

        except SelecTreeResultNotFoundError:
            logging.error(f"Selec Tree result not found while mapping {species[i]}")
            urlPaths.loc[i] = 0

        except Exception as err:
            logging.error(f"Exception while mapping {species[i]}: {err=}")
            urlPaths.loc[i] = 0

        if show_progress:
            print(f"{i + 1}/{num_species}", end="\r")

            if i + 1 == num_species:
                # new line to overwrite carriage
                print()

    mapped_series = pd.concat([species, urlPaths], axis=1).rename(
        {0: "urlPath", "0": "qSpecies"}, axis=1
    )

    return mapped_series


if __name__ == "__main__":
    start_time = time.time()
    species_path = os.path.join("src", "SF_Tree_Identifier", "data", "Species.csv")
    species_series = pd.read_csv(species_path, index_col=0).iloc[:, 0]
    species_df = assign_url_paths(species_series, show_progress=True, weight=1.2)
    species_df.to_csv(f"{FILENAME}.csv")

    # calculate number missing vs complete
    num_missing = species_df.loc[species_df.urlPath == 0].urlPath.size
    total_species, _ = species_df.shape

    # calculate time taken
    time_taken = time.time() - start_time
    mins = int(time_taken // 60)
    seconds = time_taken % 60

    # print results
    print(f"Done! Time taken: {mins}min {seconds:.0f}s")
    print(f"Number of species missing paths: {num_missing}/{total_species}")
    # if score_count[1] > 0:
    # print(f'Multi result occured {score_count[1]} times, average score was {score_count[0] / score_count[1]: .0f}')
