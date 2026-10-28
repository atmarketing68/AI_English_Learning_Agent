"""Load the rows saved by dump_db.py into a fresh PostgreSQL database.

Run AFTER the schema exists (`alembic upgrade head` from agen-backend) and with a superuser-capable
role (the default `postgres` user of the official Docker image works).
Usage: python restore_db.py "<new_db_url>" <dir_with_*.copy_and_manifest.json>
Existing rows (e.g. seeded achievements/curriculum) are replaced by the backup.
"""
import json
import os
import sys

import psycopg2

url, data_dir = sys.argv[1], sys.argv[2]
manifest = json.load(open(os.path.join(data_dir, "manifest.json"), encoding="utf-8"))
tables = [t for t in manifest["tables"] if t != "alembic_version"]  # keep the new server's schema version

conn = psycopg2.connect(url)
cur = conn.cursor()
cur.execute("select table_name from information_schema.tables where table_schema='public' and table_type='BASE TABLE'")
present = {r[0] for r in cur.fetchall()}
missing = [t for t in tables if t not in present]
if missing:
    sys.exit(f"Schema is missing tables {missing}. Run `alembic upgrade head` first.")

cur.execute("set session_replication_role = replica")        # skip FK checks while loading
cur.execute("truncate " + ", ".join(f'"{t}"' for t in tables))
for t in tables:
    cols = ", ".join(f'"{c}"' for c in manifest["columns"][t])
    with open(os.path.join(data_dir, f"{t}.copy"), "r", encoding="utf-8") as f:
        cur.copy_expert(f'COPY "{t}" ({cols}) FROM STDIN', f)
cur.execute("set session_replication_role = default")
conn.commit()

bad = 0
for t in tables:
    cur.execute(f'select count(*) from "{t}"')
    n, want = cur.fetchone()[0], manifest["tables"][t]["rows"]
    if n != want:
        bad += 1
        print(f"MISMATCH {t}: restored {n}, expected {want}")
print("restore OK: all row counts match" if not bad else f"{bad} tables differ")
conn.close()
