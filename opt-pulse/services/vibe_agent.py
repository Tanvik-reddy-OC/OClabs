import os
import logging
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional

import polars as pl
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

logger = logging.getLogger(__name__)

# --------------------------------------------------
# 1. Improved Output Schema (Matches Reference Images)
# --------------------------------------------------
class VibeProfilerOutput(BaseModel):
    vibe_title: str = Field(description="A catchy title like 'Weekend Warrior' or 'The Green Flag'")
    vibe_subtitle: str = Field(description="A short, witty description of their shopping style.")
    top_category: str = Field(description="Their most purchased category.")
    peak_shopping_day: str = Field(description="Day of the week they shop the most.")
    color_vibe: str = Field(description="A hex code representing their shopping mood (e.g. #FF00FF).")
    color_name: str = Field(description="Creative name for the color (e.g. 'Midnight Blue').")
    fun_fact: str = Field(description="A hyper-specific generated stat, e.g., 'You bought 12 Green Shirts'.")
    spend_tier: str = Field(description="Calculated tier: 'Savvy Saver', 'Wallet MVP', or 'Big Spender'.")

# --------------------------------------------------
# Vibe Agent
# --------------------------------------------------
class VibeAgent:

    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model="gpt-4o",
            temperature=0.4 # Slightly higher creativity
        )

        self.parser = JsonOutputParser(pydantic_object=VibeProfilerOutput)

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a witty retail data analyst creating a 'Spotify Wrapped' style summary."),
            ("human",
             """Analyze this customer's raw data and generate a Vibe Card profile.
             
             Data Context:
             {transaction_summary}
             
             Task:
             1. Assign a 'Vibe Title' based on their top day or category (e.g., if Saturday -> 'Weekend Warrior').
             2. Create a 'Fun Fact' based on the specific items or categories provided.
             3. Choose a color vibe that matches their items.

             {format_instructions}
             """)
        ]).partial(format_instructions=self.parser.get_format_instructions())

        self.chain = self.prompt | self.llm | self.parser

    # --------------------------------------------------
    def process(self, params, image_service=None, data_engine=None):

        contact_id = params["user_id"]

        # Fetch Data
        df: pl.DataFrame = (
            data_engine
            .get_transaction_history(contact_id)
            .collect()
        )

        if df.is_empty():
            return {"error": "No purchase history found."}

        # --------------------------------------------------
        # 2. Pre-Calculate Specific Metrics (Hard Stats)
        # --------------------------------------------------
        
        # Calculate Top Day of Week
        df = df.with_columns(pl.col("sales_date").dt.strftime("%A").alias("day_name"))
        top_day = df["day_name"].mode().first() if not df["day_name"].is_null().all() else "Unknown"
        
        # Calculate Top Category
        top_category = df["item_category"].mode().first() if "item_category" in df.columns else "General"
        
        # Calculate Totals
        total_spend = df["sales_price"].sum()
        total_items = df["quantity"].sum()

        # Create a text summary for the LLM to analyze
        transaction_summary = f"""
        Customer ID: {contact_id}
        Top Shopping Day: {top_day}
        Top Category: {top_category}
        Total Spend: {total_spend}
        Total Items: {total_items}
        Sample of recent items bought: {df["description"].head(5).to_list()}
        """

        # Invoke LLM
        ai_output = self.chain.invoke({"transaction_summary": transaction_summary})

        # Return combined data
        return {
            "user_id": contact_id,
            "raw_stats": {
                "total_spend": round(total_spend, 2),
                "total_items": total_items,
                "top_day": top_day
            },
            "ai_content": ai_output
        }