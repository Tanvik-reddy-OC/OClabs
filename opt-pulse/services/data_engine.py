import polars as pl
from core.database import get_duckdb_connection, load_csvs_to_duckdb
from typing import Dict, Any


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

    def get_campaign_performance(self) -> pl.LazyFrame:
        """
        Join templates with campaign metrics and calculate success rate.
        """
        sql = """
        SELECT
            t.id AS template_id,
            t.msg_content,
            COUNT(*) FILTER (WHERE cm.event_type = 'DELIVERED') AS delivered,
            COUNT(*) FILTER (WHERE cm.event_type = 'CLICKED') AS clicked,
            CASE
                WHEN COUNT(*) FILTER (WHERE cm.event_type = 'DELIVERED') = 0 THEN 0
                ELSE
                    COUNT(*) FILTER (WHERE cm.event_type = 'CLICKED') * 1.0
                    / COUNT(*) FILTER (WHERE cm.event_type = 'DELIVERED')
            END AS success_rate
        FROM templates t
        LEFT JOIN campaign_metrics cm
            ON t.id = cm.campaign_id
        GROUP BY t.id, t.msg_content
        """
        return self._execute_duckdb_query(sql)

    def get_user_group_profile(self, cid_start: int, cid_end: int) -> Dict[str, Any]:
        """
        Builds an aggregated user profile for a CID range.
        """
        sql = f"""
        SELECT
            c.gender,
            c.city,
            c.loyalty_customer,
            COUNT(*) AS user_count,
            AVG(s.quantity * s.sales_price) AS avg_spend
        FROM contacts c
        LEFT JOIN sales s ON c.cid = s.cid
        WHERE c.cid BETWEEN {cid_start} AND {cid_end}
        GROUP BY c.gender, c.city, c.loyalty_customer
        """
        lf = self._execute_duckdb_query(sql)
        df = lf.collect()

        if df.is_empty():
            raise RuntimeError("No users found for given CID range")

        return {
            "total_users": df["user_count"].sum(),
            "gender_distribution": df.group_by("gender").agg(pl.sum("user_count")).to_dicts(),
            "city_distribution": df.group_by("city").agg(pl.sum("user_count")).to_dicts(),
            "loyalty_split": df.group_by("loyalty_customer").agg(pl.sum("user_count")).to_dicts(),
            "avg_spend": round(df["avg_spend"].mean(), 2)
        }
    def format_group_profile(profile: Dict[str, Any]) -> str:
        return f"""
    User Group Summary:
    - Total Users: {profile['total_users']}
    - Gender Distribution: {profile['gender_distribution']}
    - City Distribution: {profile['city_distribution']}
    - Loyalty Split: {profile['loyalty_split']}
    - Average Spend: {profile['avg_spend']}
    """

    def get_contacts_loyalty(self) -> pl.LazyFrame:
        sql = """
        SELECT
            contact_id,
            total_loyalty_earned,
            loyalty_balance,
            created_date,
            cummulative_purchase_value
        FROM contacts_loyalty
        """
        return self._execute_duckdb_query(sql)

    def get_loyalty_by_contact(self, contact_id: int) -> pl.LazyFrame:
        sql = f"""
        SELECT *
        FROM contacts_loyalty
        WHERE contact_id = {contact_id}
        """
        return self._execute_duckdb_query(sql)

    def get_contacts_with_loyalty_balance_above(self, threshold: float) -> pl.LazyFrame:
        sql = f"""
        SELECT *
        FROM contacts_loyalty
        WHERE loyalty_balance > {threshold}
        """
        return self._execute_duckdb_query(sql)

    def get_loyalty_aggregate(self) -> Dict[str, Any]:
        sql = """
        SELECT
            SUM(total_loyalty_earned) AS total_loyalty_earned,
            SUM(loyalty_balance) AS total_loyalty_balance,
            SUM(cummulative_purchase_value) AS total_purchase_value
        FROM contacts_loyalty
        """
        lf = self._execute_duckdb_query(sql)
        df = lf.collect()
        return df[0].to_dict() if not df.is_empty() else {}
        
    def get_contact_ids(self) -> pl.LazyFrame:
        sql = """
        SELECT cid
        FROM contacts
        """
        return self._execute_duckdb_query(sql)
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
