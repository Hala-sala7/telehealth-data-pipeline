import duckdb
from pathlib import Path

# Bronze layer: load the raw CSV files into DuckDB exactly as they are.
# All columns are kept as text so nothing changes on the way in.
# Two extra columns help us track where each row came from:
#   _source_file -> the file name
#   _ingested_at -> when it was loaded

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / 'data' / 'raw'
DB_PATH = ROOT / 'data' / 'warehouse.duckdb'


def main():
    print("Loading bronze layer...")

    files = sorted(RAW_DIR.glob('*.csv'))
    if len(files) == 0:
        raise SystemExit("No raw files found. Run scripts/generate_data.py first.")

    con = duckdb.connect(str(DB_PATH))
    con.execute("CREATE SCHEMA IF NOT EXISTS bronze")

    for f in files:
        table = f'bronze.{f.stem}'

        con.execute(f"""
            CREATE OR REPLACE TABLE {table} AS
            SELECT *,
                '{f.name}' AS _source_file,
                current_timestamp AS _ingested_at
            FROM read_csv('{f.as_posix()}', header = true, all_varchar = true)
        """)

        n_rows = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        print(f"  {table}:", n_rows, "rows")

    con.close()


if __name__ == '__main__':
    main()
