import difflib
import os

url_finder = open('url_finder.log').read().splitlines(keepends=True)
url_finder_partial = open('url_finder_partial.log').read().splitlines(keepends=True)

d = difflib.Differ()

result = list(d.compare(url_finder, url_finder_partial))

with open('non_vs_partial.txt', 'w') as fp:
    for line in result:
        fp.write(line)
