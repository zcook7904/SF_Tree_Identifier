import argparse
import sys
import os
from pathlib import Path # if you haven't already done so

# https://stackoverflow.com/questions/16981921/relative-imports-in-python-3

file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

# Additionally remove the current file's directory from sys.path
try:
    sys.path.remove(str(parent))
except ValueError: # Already removed
    pass

from SF_Tree_Identifier import identify_trees, test

def main():
    """"""
    parser = argparse.ArgumentParser(description='Get the tree species of the tree at the given address.')
    g = parser.add_mutually_exclusive_group()
    g.add_argument('address', nargs='*', default='',
                        help='a street address located in San Francisco, CA')
    g.add_argument('--test', '-t', action='store_true', help='run test suite')
    args = parser.parse_args()

    if args.test:
        test.test()
    elif args.address != '':
        # prints found trees
        address = ' '.join(args.address)
        returned_trees = SF_Tree_Identifier.get_trees(address)
        SF_Tree_Identifier.print_trees(returned_trees)

    else:
        #displays help message if no arg given
        args = parser.parse_args(['-h'])


if __name__ == '__main__':
    main()
