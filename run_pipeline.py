import subprocess
import sys
from pathlib import Path

import duckdb

# Runs the whole pipeline:
# 1. generate raw data
# 2. load bronze (Python + DuckDB)
# 3. build + test silver and gold (dbt)
# 4. print how many rows are in each table

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scripts'))

import generate_data
import load_bronze


def run_dbt():
    print("Building silver and gold layers with dbt...")
    result = subprocess.run(
        ['dbt', 'build', '--project-dir', 'dbt', '--profiles-dir', 'dbt'],
        cwd=ROOT
    )
    if result.returncode != 0:
        raise SystemExit("dbt build failed, check the output above.")


def print_summary():
    con = duckdb.connect(str(ROOT / 'data' / 'warehouse.duckdb'), read_only=True)

    tables = con.execute("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema IN ('bronze', 'silver', 'gold')
        ORDER BY table_schema = 'gold', table_schema = 'silver', table_name
    """).fetchall()

    print("\nRows per table:")
    for schema, table in tables:
        n_rows = con.execute(f"SELECT count(*) FROM {schema}.{table}").fetchone()[0]
        print(f"  {schema}.{table}:", n_rows)

    con.close()


if __name__ == '__main__':
    generate_data.main()
    load_bronze.main()
    run_dbt()
    print_summary()
