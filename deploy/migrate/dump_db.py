"""Dump every table of the Render Postgres database to COPY-format files (data only).

The schema is rebuilt on the new server with `alembic upgrade head`; this script only saves the rows.
Usage: python dump_db.py <db_url_file> <out_dir>
"""
import hashlib
import json
import os
import sys

import psycopg2

url_file, out_dir = sys.argv[1], sys.argv[2]
url = open(url_file, encoding="ascii").read().strip()
if "sslmode" not in url:
    url += ("&" if "?" in url else "?") + "sslmode=require"
os.makedirs(out_dir, exist_ok=True)

conn = psycopg2.connect(url, connect_timeout=30)
conn.set_session(readonly=True, isolation_level="REPEATABLE READ")  # one consistent snapshot
cur = conn.cursor()
cur.execute("select version()")
version = cur.fetchone()[0]
cur.execute("select current_database(), pg_size_pretty(pg_database_size(current_database()))")
dbname, size = cur.fetchone()
cur.execute("""select table_name from information_schema.tables
               where table_schema = 'public' and table_type = 'BASE TABLE' order by table_name""")
tables = [r[0] for r in cur.fetchall()]

manifest = {"postgres": version, "database": dbname, "size": size, "tables": {}}
for t in tables:
    path = os.path.join(out_dir, f"{t}.copy")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        cur.copy_expert(f'COPY "{t}" TO STDOUT', f)
    cur.execute(f'select count(*) from "{t}"')
    n = cur.fetchone()[0]
    sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
    manifest["tables"][t] = {"rows": n, "sha256": sha}
    print(f"{t}: {n} rows")

# column order per table, so the restore can name columns explicitly
cur.execute("""select table_name, column_name from information_schema.columns
               where table_schema = 'public' order by table_name, ordinal_position""")
cols = {}
for tname, cname in cur.fetchall():
    cols.setdefault(tname, []).append(cname)
manifest["columns"] = cols
json.dump(manifest, open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("tables:", len(tables), "total rows:", sum(v["rows"] for v in manifest["tables"].values()), "| db size:", size)
conn.close()
