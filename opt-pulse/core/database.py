import os
import duckdb

def get_duckdb_connection():
    """Initializes and returns a DuckDB in-memory connection."""
    # For a persistent DB, specify a file path: duckdb.connect('my_database.duckdb')
    return duckdb.connect(database=':memory:')

def load_csvs_to_duckdb(duckdb_conn):
    """
    Loads CSV files from the data directory into DuckDB tables.
    """
    # Define paths to CSV files
    # Assuming the 'data' directory is in the project root, one level up from 'core'
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    
    transactions_csv = os.path.join(data_dir, "transactions.csv")
    customers_csv = os.path.join(data_dir, "customers.csv")

    if not os.path.exists(transactions_csv) or not os.path.exists(customers_csv):
         raise FileNotFoundError(f"CSV files not found in {data_dir}. Please ensure transactions.csv and customers.csv exist.")

    # Create tables from CSVs
    # DuckDB can read directly from CSVs using read_csv_auto
    print(f"Loading transactions from {transactions_csv}...")
    duckdb_conn.execute(f"CREATE OR REPLACE TABLE transactions AS SELECT * FROM read_csv_auto('{transactions_csv}');")
    
    print(f"Loading customers from {customers_csv}...")
    duckdb_conn.execute(f"CREATE OR REPLACE TABLE customers AS SELECT * FROM read_csv_auto('{customers_csv}');")
    
    print("CSV data loaded into DuckDB tables 'transactions' and 'customers'.")

# Example usage (for testing, not for production direct execution)
if __name__ == "__main__":
    try:
        duckdb_conn = get_duckdb_connection()
        print("DuckDB connection established.")
        
        load_csvs_to_duckdb(duckdb_conn)
        print("Attempting to query tables...")
        
        # Example: List tables
        tables = duckdb_conn.execute("SHOW TABLES;").fetchdf()
        print("Tables in DuckDB:")
        print(tables)
        
    except Exception as e:
        print(f"An error occurred: {e}")