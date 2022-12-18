import unittest
import os
import sys
import pandas as pd

# adds python module to path
path_to_append = os.path.join(".", "src")
sys.path.append(path_to_append)
from url_finder import url_finder


class MatchScoresTestCase(unittest.TestCase):
    def test_match_common_name_match_scores(self):
        specie = url_finder.Specie(
            scientific_name="Corymbia ficifolia", common_name="Red Flowering Gum"
        )
        other_specie = url_finder.Specie(
            scientific_name="Corymbia otherfolia", common_name="Red Flowering Gum"
        )
        scores = url_finder.get_common_name_match_scores(specie, [other_specie])
        self.assertTrue(scores[0] == 100)


class SelecTreeFinderTestCase(unittest.TestCase):
    def test_good_name(self):
        specie = url_finder.Specie(
            scientific_name="Corymbia ficifolia", common_name="Red Flowering Gum"
        )
        self.assertTrue(url_finder.get_selec_tree_url_path(specie) == 540)

    def test_bad_name(self):
        with self.assertRaises(url_finder.SelecTreeResultNotFoundError):
            specie = url_finder.Specie(
                scientific_name="bad name", common_name="worse name"
            )
            self.assertTrue(url_finder.get_selec_tree_url_path(specie) == 0)

    def test_other_name(self):
        specie = url_finder.Specie(
            formatted_name="Lophostemon confertus :: Brisbane Box"
        )
        self.assertFalse(url_finder.get_selec_tree_url_path(specie) == 673)

    def test_other_other_name(self):
        specie = url_finder.Specie(
            formatted_name="Cupressus macrocarpa :: Monterey Cypress"
        )
        self.assertFalse(url_finder.get_selec_tree_url_path(specie) == 673)

    def test_other_final_name(self):
        specie = url_finder.Specie(formatted_name="Salix spp :: Willow")
        self.assertFalse(url_finder.get_selec_tree_url_path(specie) == 673)

    def test_other_other_final_name(self):
        specie = url_finder.Specie(formatted_name="patanus racemosa ::")
        self.assertFalse(url_finder.get_selec_tree_url_path(specie) == 673)

    def test_other_other_final_name(self):
        specie = url_finder.Specie(formatted_name="Brachychiton discolor ::")
        self.assertFalse(url_finder.get_selec_tree_url_path(specie) == 673)


class AssignUrlTestCase(unittest.TestCase):
    def test_url_assigned(self):
        species = pd.Series(
            ["Corymbia ficifolia :: Red Flowering Gum", "bad name 123 :: worse name"],
            name="qSpecies",
            dtype="string",
        )
        assigned_species = url_finder.assign_url_paths(species, time_buffer=False)
        self.assertTrue(assigned_species.iloc[0, 1] == 540)

    def test_bad_species_assigned_0(self):
        species = pd.Series(
            ["Corymbia ficifolia :: Red Flowering Gum", "bad name 123 :: worse name"],
            name="qSpecies",
            dtype="string",
        )
        assigned_species = url_finder.assign_url_paths(species, time_buffer=False)
        self.assertTrue(assigned_species.iloc[1, 1] == 0)

    def test_check_returned_id(self):
        pass


class SplitqSpecieNameTestCase(unittest.TestCase):
    def test_split_with_common_name(self):
        specie_name = "Corymbia ficifolia :: Red Flowering Gum"
        specie = url_finder.Specie(formatted_name=specie_name)
        self.assertTrue(specie.common_name == "Red Flowering Gum")
        self.assertTrue(specie.scientific_name == "Corymbia ficifolia")

    def test_split_with_no_common_name(self):
        specie_name = "Corymbia ficifolia ::"
        specie = url_finder.Specie(formatted_name=specie_name)
        self.assertIsNone(specie.common_name)
        self.assertTrue(specie.scientific_name == "Corymbia ficifolia")

    def test_split_with_common_name_2(self):
        specie_name = "Salix spp :: Willow"
        specie = url_finder.Specie(formatted_name=specie_name)
        self.assertTrue(specie.common_name == "Willow")
        self.assertTrue(specie.scientific_name == "Salix spp")


if __name__ == "__main__":
    unittest.main()
