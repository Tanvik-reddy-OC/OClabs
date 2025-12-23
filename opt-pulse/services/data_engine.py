import polars as pl
import duckdb
from core.database import get_duckdb_connection, load_csvs_to_duckdb

class DataEngine:
    def __init__(self):
        self.duckdb_conn = get_duckdb_connection()
        try:
            load_csvs_to_duckdb(self.duckdb_conn)
            print("CSV data loaded into DuckDB successfully for DataEngine.")
        except Exception as e:
            print(f"Error loading CSVs into DuckDB in DataEngine: {e}")
            # Depending on error handling strategy, might re-raise or handle gracefully
            raise

    def _execute_duckdb_query(self, sql_query: str) -> pl.LazyFrame:
        """
        Executes a SQL query against DuckDB and returns the result as a Polars LazyFrame.
        """
        return self.duckdb_conn.sql(sql_query).lazy()

    def get_transaction_history(self, user_id: str) -> pl.LazyFrame:
        """
        Fetches transaction history for a given user_id from CSV data via DuckDB.
        Returns a Polars LazyFrame.
        """
        # Tables 'transactions' and 'customers' are created in the default schema by load_csvs_to_duckdb
        sql_query = f"""
            SELECT 
                transaction_id,
                user_id,
                item_id,
                quantity,
                price,
                transaction_timestamp
            FROM transactions
            WHERE user_id = '{user_id}'
        """
        return self._execute_duckdb_query(sql_query)

    def get_customer_metadata(self, user_id: str) -> pl.LazyFrame:
        """
        Fetches customer metadata for a given user_id from CSV data via DuckDB.
        Returns a Polars LazyFrame.
        """
        sql_query = f"""
            SELECT 
                user_id,
                name,
                email,
                address,
                loyalty_status,
                signup_date
            FROM customers
            WHERE user_id = '{user_id}'
        """
        return self._execute_duckdb_query(sql_query)

    # Example of a more complex, normalized pipeline (conceptual, not fully implemented for all fields)
    def get_user_data_pipeline(self, user_id: str) -> pl.LazyFrame:
        """
        Combines transaction history and customer metadata for a user.
        Returns a Polars LazyFrame.
        """
        transactions = self.get_transaction_history(user_id)
        customers = self.get_customer_metadata(user_id)

        # Example of joining and basic normalization (e.g., calculating total spend per transaction)
        # No business logic, just data preparation.
        user_data = (
            transactions
            .join(customers, on="user_id", how="left")
            .with_columns(
                (pl.col("quantity") * pl.col("price")).alias("total_item_spend")
            )
        )
        return user_data

# Example usage (for testing, not for production direct execution)
if __name__ == "__main__":
    try:
        data_engine = DataEngine()
        user_id_example = "user123" # Replace with an actual user_id from your CSV data

        print(f"\nFetching transaction history for {user_id_example}...")
        transactions_lf = data_engine.get_transaction_history(user_id_example)
        print("Transaction History Schema:")
        print(transactions_lf.schema)
        # To see data, uncomment .fetch():
        # print(transactions_lf.fetch()) 

        print(f"\nFetching customer metadata for {user_id_example}...")
        customer_lf = data_engine.get_customer_metadata(user_id_example)
        print("Customer Metadata Schema:")
        print(customer_lf.schema)
        # To see data, uncomment .fetch():
        # print(customer_lf.fetch())

        print(f"\nFetching combined user data pipeline for {user_id_example}...")
        combined_data_lf = data_engine.get_user_data_pipeline(user_id_example)
        print("Combined Data Pipeline Schema:")
        print(combined_data_lf.schema)
        # To see data, uncomment .fetch():
        # print(combined_data_lf.fetch())

    except Exception as e:
        print(f"An error occurred in DataEngine example: {e}")