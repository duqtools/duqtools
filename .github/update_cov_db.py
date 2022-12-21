import sqlite3
from pathlib import Path

conn = sqlite3.connect('.coverage')
cwd = str(Path.cwd())

print(list(conn.execute('select * from file'))[0])

for (idx, path) in conn.execute('select * from file'):
    new_path = path.replace('/__w/duqtools/duqtools', cwd)

    q = 'update file set path = :new_path where id = :idx;'

    conn.execute(q, {'idx': idx, 'new_path': new_path})

conn.commit()

print(list(conn.execute('select * from file'))[0])

conn.close()
