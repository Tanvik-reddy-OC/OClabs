import polars as pl
from core.database import get_duckdb_connection, load_csvs_to_duckdb


class DataEngine:
    def __init__(self):
        self.duckdb_conn = get_duckdb_connection()
        load_csvs_to_duckdb(self.duckdb_conn)
        print("CSV data loaded into DuckDB successfully for DataEngine.")

    def _execute_duckdb_query(self, sql_query: str) -> pl.LazyFrame:
        """
        Executes a SQL query in DuckDB and returns a Polars LazyFrame.
        """
        arrow_table = self.duckdb_conn.execute(sql_query).arrow()
        return pl.from_arrow(arrow_table).lazy()

    # -------------------------------
    # SALES / TRANSACTIONS
    # -------------------------------
    def get_sales_history(self, cid: str) -> pl.LazyFrame:
        """
        Fetch sales history for a customer.
        """
        sql = f"""
        SELECT
            s.sales_id,
            s.sales_date,
            s.quantity,
            s.sales_price,
            s.discount,
            s.sku,
            s.item_sid,
            c.cid,
            c.first_name,
            c.last_name,
            c.gender,
            c.city,
            c.loyalty_customer
        FROM sales s
        JOIN contacts c ON s.cid = c.cid
        WHERE s.cid = '{cid}'
        """
        return self._execute_duckdb_query(sql)

    # -------------------------------
    # CUSTOMER PROFILE
    # -------------------------------
    def get_customer_profile(self, cid: str) -> pl.LazyFrame:
        """
        Fetch customer metadata.
        """
        sql = f"""
        SELECT
            cid,
            first_name,
            last_name,
            gender,
            city,
            birth_day,
            loyalty_customer,
            created_date
        FROM contacts
        WHERE cid = '{cid}'
        """
        return self._execute_duckdb_query(sql)

    # -------------------------------
    # SKU / PRODUCT DETAILS
    # -------------------------------
    def get_product_catalog(self) -> pl.LazyFrame:
        """
        Fetch SKU master data.
        """
        sql = """
        SELECT
            sku_id,
            sku,
            description,
            list_price,
            item_category,
            item_sid,
            vendor_code,
            department_code,
            dcs,
            created_date
        FROM sku
        """
        return self._execute_duckdb_query(sql)

    # -------------------------------
    # SALES + SKU ENRICHMENT
    # -------------------------------
    def get_enriched_sales(self, cid: str) -> pl.LazyFrame:
        """
        Sales joined with SKU data.
        """
        sql = f"""
            SELECT
            s.cid,
            s.sales_id,
            s.sales_date,
            s.quantity,
            s.sales_price,
            s.discount,
            p.description,
            p.item_category,
            p.vendor_code,
            p.department_code
        FROM sales s
        LEFT JOIN sku p ON s.item_sid = p.item_sid
        WHERE s.cid = '{cid}'
        """
        return self._execute_duckdb_query(sql)

    # -------------------------------
    # CAMPAIGN METRICS
    # -------------------------------
    def get_campaign_events(self, campaign_id: str) -> pl.LazyFrame:
        """
        Fetch campaign events.
        """
        sql = f"""
        SELECT
            event_id,
            campaign_id,
            event_type,
            event_date
        FROM campaign_metrics
        WHERE campaign_id = '{campaign_id}'
        """
        return self._execute_duckdb_query(sql)

    # -------------------------------
    # USER ANALYTICS PIPELINE (CORE)
    # -------------------------------
    def get_user_analytics_pipeline(self, cid: str) -> pl.LazyFrame:
        """
        Unified analytics view for a customer.
        (used for Vibe Report / Smart Receipts)
        """
        sales = self.get_enriched_sales(cid)
        customer = self.get_customer_profile(cid)

        return (
            sales
            .join(customer, on="cid", how="left")
            .with_columns(
                (pl.col("quantity") * pl.col("sales_price")).alias("gross_spend"),
                (pl.col("quantity") * pl.col("discount")).alias("discount_value")
            )
        )


# -------------------------------
# Local test
# -------------------------------
if __name__ == "__main__":
    engine = DataEngine()
    test_cid = "20186130"  # replace with actual cid

    lf = engine.get_user_analytics_pipeline(test_cid)
    print(lf.collect_schema())

    # Debug preview
    # print(lf.fetch())
