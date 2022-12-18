import os
import pandas as pd

ORIGINAL_PATH = os.path.join('..', '..', 'original_data', 'Processed_Street_Tree_List.csv')
ACCEPTABLE_SITE_INFO = ['Front Yard :', 'Front Yard : Cutout', 'Front Yard : Pot',
                        'Front Yard : Yard', 'Hanging basket : Cutout', 'Hanging basket : Yard',
                        'Median :', 'Median : Cutout', 'Median : Hanging Pot', 'Median : Yard',
                        'Sidewalk: Curb side :',
                        'Sidewalk: Curb side : Cutout',
                        'Sidewalk: Curb side : Hanging Pot', 'Sidewalk: Curb side : Pot',
                        'Sidewalk: Curb side : Yard',
                        'Sidewalk: Property side :', 'Sidewalk: Property side : Cutout',
                        'Sidewalk: Property side : Pot',
                        'Sidewalk: Property side : Yard']
NON_SPECIES_CATEGORIES = ['::', ':: To Be Determine', ':: Tree', 'Tree(s) ::',
                          'Potential Site :: Potential Site', 'Private shrub :: Private Shrub', 'Shrub :: Shrub',
                          'Private shrub :: Private Shrub']
CLEANED_PATH = os.path.join('..', 'Cleaned_Street_Tree_List.csv')


def load_original_data(path: str) -> pd.DataFrame:
    """Loads the original data csv and returns a pandas dataframe of the csv file."""
    try:
        return pd.read_csv(path).set_index('TreeID')
    except FileNotFoundError:
        raise FileNotFoundError('Cannot find original Process_Street_Tree_List.csv file')

def fix_site_orders(tree_list: pd.DataFrame) -> pd.DataFrame:
    """Changes site seemingly faulty SiteOrders to more reasonable ones."""
    tree_list.loc[98278, 'SiteOrder'] = 23
    tree_list.loc[98279, 'SiteOrder'] = 24
    tree_list.loc[96618, 'SiteOrder'] = 1
    tree_list.loc[137894, 'SiteOrder'] = 2

    return tree_list

def select_acceptable_site_info(tree_list: pd.DataFrame, acceptable_site_info: list[str]) -> pd.DataFrame:
    """Returns the tree list with trees that are located at the passed acceptable site info list."""
    return tree_list.loc[tree_list['qSiteInfo'].isin(acceptable_site_info)]

def remove_non_species_categories(tree_list: pd.DataFrame, non_species_categories: list[str]) -> pd.DataFrame:
    """Returns the tree list with the given non_species_categories filtered out."""
    return tree_list.loc[~tree_list.qSpecies.isin(non_species_categories)]

def remove_stair_addresses(tree_list: pd.DataFrame) -> pd.DataFrame:
    """Remove 'stairway' addresses from tree list."""
    return tree_list.loc[~tree_list.qAddress.str.contains('STAIRWAY')]


def main():
    original_data = load_original_data(ORIGINAL_PATH)

    data = original_data.loc[:, ['qSpecies', 'qAddress', 'SiteOrder', 'qSiteInfo']].dropna(subset='qAddress')
    data[['SiteOrder']] = data[['SiteOrder']].fillna(1)

    data = fix_site_orders(data)
    data = select_acceptable_site_info(data, ACCEPTABLE_SITE_INFO)

    data = data.astype({'qSpecies': 'category', 'qAddress': 'string', 'SiteOrder': 'int8', 'qSiteInfo': 'category'})
    data = remove_non_species_categories(data, NON_SPECIES_CATEGORIES)

    # remove (revised) addresses
    data.qAddress = data.qAddress.str.replace('[(]?revised[)]?', '', regex=True)

    data = remove_stair_addresses(data)

    data.to_csv(CLEANED_PATH)

if __name__ == '__main__':
    main()