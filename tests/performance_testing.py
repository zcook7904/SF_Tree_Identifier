import logging
from timeit import timeit
import os
import sys
from datetime import datetime
import pandas as pd

# adds python module to path
path_to_append = os.path.join('.', 'src')
sys.path.append(path_to_append)
from SF_Tree_Identifier import SF_Tree_Identifier

logging.basicConfig(level=logging.ERROR)

number=1000
test_addresses = ['1470 Valencia St', '1470 valenci street', '1468 Valencia St', '900 Brotherhood Way']
def main():
    benchmarks = pd.DataFrame(columns=['datetime', *test_addresses])

    benchmarks.loc[0, 'datetime'] = datetime.now().isoformat()

    for address in test_addresses:
        time = timeit(lambda: SF_Tree_Identifier.main(address), number=number) / number #s
        print(f'{address} - time: {time: .5f}s')
        benchmarks.loc[0,address] = time

    print(f"Total: {benchmarks.drop('datetime', axis=1).iloc[0].sum(): .5f}s")
    benchmarks.to_csv('benchmarks.csv', mode='a')

if __name__ == "__main__":
    main()
