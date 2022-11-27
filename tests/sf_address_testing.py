import logging
import os
import sys
import json
import time
import pandas as pd

# adds python module to path
path_to_append = os.path.join('.', 'src')
sys.path.append(path_to_append)
from SF_Tree_Identifier import SF_Tree_Identifier, Address

os.remove('sf_address_testing.log')
logging.basicConfig(level=logging.ERROR, filename='sf_address_testing.log')

def main():

    with open('addresses.json', 'r') as fp:
        addresses = json.load(fp)

    total_addresses = len(addresses)
    correct_addresses = 0

    start_time = time.time()

    for i, address in enumerate(addresses):
        try:
            SF_Tree_Identifier.main(address)
            correct_addresses += 1
        except Exception as err:
            logging.error(f'{address}: {err}')

        print(f'{i + 1}/{total_addresses} complete', end='\r')

    print(f'\nFinished, trees were found at {correct_addresses}/{total_addresses}')
    total_time = time.time() - start_time

    print(f'Total time: {total_time:.1f}s')
    print(f'Average time: {total_time / total_addresses: .5f}s')
if __name__ == "__main__":
    main()
