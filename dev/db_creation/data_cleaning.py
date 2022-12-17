import os
import pandas as pd

def load_original_data(path: str) -> pd.DataFrame:
    """Loads the original data csv and returns a pandas dataframe of the csv file."""
    try:
        return pd.read_csv(path).set_index('TreeID')
    except FileNotFoundError:
        raise FileNotFoundError('Cannot find original Process_Street_Tree_List.csv file')

def main():
    original_path = os.path.join('..', '..', 'original_data', 'Processed_Street_Tree_List.csv')
    original_data = load_original_data(original_path)

    data = original_data.loc[:, ['qSpecies', 'qAddress', 'SiteOrder', 'qSiteInfo']].dropna(subset='qAddress')
    data[['SiteOrder']] = data[['SiteOrder']].fillna(1)


if __name__ == '__main__':
    main()