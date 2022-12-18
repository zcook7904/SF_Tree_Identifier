import sqlite3
import os

os.chdir("..")
path = f"src//SF_Tree_Identifier//data//SF_trees.db"

con = sqlite3.connect(path)
cur = con.cursor()
query = """
PRAGMA foreign_keys=off
ALTER TABLE 'species' RENAME to old_species

CREATE TABLE "species" (
"index" INTEGER PRIMARY KEY,
  "qSpecies" TEXT,
  "urlPath" INTEGER
)

"""
result = cur.execute(query)

if result:
    if fetchall:
        result = result.fetchall()
    else:
        result = result.fetchone()

con.close()
