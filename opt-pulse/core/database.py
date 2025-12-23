import os
import duckdb

def get_duckdb_connection():
    """Initializes and returns a DuckDB in-memory connection."""
    return duckdb.connect(database=":memory:")

def load_csvs_to_duckdb(duckdb_conn):
    """
    Loads all CSV files from the data directory into DuckDB tables.
    Table name = CSV filename (without .csv)
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")

    csv_files = {
        "campaign_metrics": "campaign_metrics.csv",
        "contacts": "contacts.csv",
        "sales": "sales.csv",
        "sku": "sku.csv",
        "templates": "templates.csv",
    }

    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    for table_name, csv_file in csv_files.items():
        csv_path = os.path.join(data_dir, csv_file)

        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Missing CSV file: {csv_path}")

        print(f"Loading {table_name} from {csv_path}...")
        duckdb_conn.execute(
            f"""
            CREATE OR REPLACE TABLE {table_name} AS
            SELECT *
            FROM read_csv_auto('{csv_path}', HEADER=TRUE);
            """
        )

    print("All CSVs loaded into DuckDB successfully.")

# Example usage (for testing only)
if __name__ == "__main__":
    try:
        conn = get_duckdb_connection()
        print("DuckDB connection established.")

        load_csvs_to_duckdb(conn)

        print("\nTables in DuckDB:")
        print(conn.execute("SHOW TABLES;").fetchdf())

    except Exception as e:
        print(f"An error occurred: {e}")
