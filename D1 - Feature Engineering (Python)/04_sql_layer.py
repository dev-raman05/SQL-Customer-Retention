# Step 4 - Load final customer table into SQLite and run the query layer.
# Input:  data/customers_loyalty.csv (3,900 x 27, from 03_loyalty.py)
# Output: data/retention.db (table: customers) + console results of every block
# The graded artifact is sql/segmentation_queries.sql; this script executes it.

import sqlite3
import pandas as pd

assert sqlite3.sqlite_version_info >= (3, 25), \
    f'SQLite {sqlite3.sqlite_version} lacks window functions (need >= 3.25)'

df = pd.read_csv('data/customers_loyalty.csv')
con = sqlite3.connect('data/retention.db')
df.to_sql('customers', con, if_exists='replace', index=False)
n_db = pd.read_sql('SELECT COUNT(*) AS n FROM customers', con)['n'][0]
assert n_db == 3900, f'db row count {n_db} != 3900'
print(f'loaded customers table: {n_db} rows | sqlite {sqlite3.sqlite_version}\n')

sql_text = open('sql/segmentation_queries.sql', encoding='utf-8').read()

# blocks are delimited by '-- =====' header lines; comments are stripped from a
# block BEFORE splitting on ';' so semicolons inside comments cannot break parsing
blocks = sql_text.split('-- =====')
for block in blocks[1:]:
    lines = block.splitlines()
    print('=====' + lines[0])
    body = '\n'.join(l for l in lines[1:] if not l.strip().startswith('--'))
    for stmt in body.split(';'):
        if not stmt.strip():
            continue
        out = pd.read_sql(stmt, con)
        print(out.to_string(index=False))
        print()
con.close()
