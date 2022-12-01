import logging
from timeit import timeit
import os
import sys
import cProfile
from datetime import datetime
import pandas as pd

# adds python module to path
path_to_append = os.path.join('.', 'src')
sys.path.append(path_to_append)
from SF_Tree_Identifier import SF_Tree_Identifier, Address

logging.basicConfig(level=logging.ERROR)

number=1000
test_addresses = ['1470 Valencia St', '1470 valenci street', '1468 Valencia St', '900 Brotherhood Way']
i = 0
def main():
    file_dir = os.path.dirname(__file__)
    benchmarks = pd.DataFrame(columns=['datetime', *test_addresses])

    benchmarks.loc[0, 'datetime'] = datetime.now().isoformat()

    for i, address in enumerate(test_addresses):
        filename =  f"{address.replace(' ', '_')}_{datetime.now().isoformat(timespec='minutes').replace(':', '-')}.prof"
        pathname = os.path.join(file_dir, 'profiles', filename)
        cProfile.run('SF_Tree_Identifier.main(test_addresses[i])', filename=pathname)

        time = timeit(lambda: SF_Tree_Identifier.main(address), number=number) / number #s
        print(f'{address} - time: {time: .5f}s')
        benchmarks.loc[0,address] = time

    print(f"Total: {benchmarks.drop('datetime', axis=1).iloc[0].sum(): .5f}s")

    filename = os.path.join(file_dir, 'benchmarks.csv')

    if os.path.exists(filename):
        benchmarks.to_csv(filename, mode='a', header=False)
    else:
        benchmarks.to_csv(filename, mode='w')


if __name__ == "__main__":
    main()
