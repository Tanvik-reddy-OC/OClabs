import os
import logging
from typing import Dict, Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI

from services.data_engine import DataEngine

# ------------------------------------------------------------------
# ENV + LOGGING
# ------------------------------------------------------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# OUTPUT SCHEMA (ONLY THIS USES BaseModel)
# ------------------------------------------------------------------
class BrandVoiceOutput(BaseModel):
    new_campaign_body: str = Field(description="Generated campaign body text")
    predicted_success_score: int = Field(ge=0, le=100)
    inferred_patterns: Dict[str, str]

# ------------------------------------------------------------------
# BRAND VOICE AGENT (SERVICE — NOT A MODEL)
# ------------------------------------------------------------------
class BrandVoiceAgent:
    def __init__(self):
        self.data_engine = DataEngine()

        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.25,
            api_key=OPENAI_API_KEY,
        )

        self.parser = JsonOutputParser(
            pydantic_object=BrandVoiceOutput
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                     "system",
                    """
You are a senior marketing intelligence AI.

You are given historical campaign messages with their real-world success rates,
and a summarized user group profile to whom the message will be sent.

Your task:
1. Identify patterns in HIGH vs LOW performing campaigns
2. Infer brand voice (tone, urgency, emoji usage, CTA style) that resonates with this user group and also is individual to that brands persona
3. Generate a NEW campaign body optimized for this user group
4. Predict the success score (0–100), based on historical data and inferred patterns

Be data-driven. Do not hallucinate unsupported patterns.
"""
                ),
                (
                    "human",
                    """
Historical Campaign Performance:
{campaign_history}

User Group Profile:
{user_profile}

{format_instructions}
"""
                ),
            ]
        ).partial(
            format_instructions=self.parser.get_format_instructions()
        )

        self.chain = self.prompt | self.llm | self.parser

    # --------------------------------------------------------------
    # PUBLIC ENTRY POINT (used by FastAPI)
    # --------------------------------------------------------------
    def process(self, params: Dict[str, Any]) -> Dict[str, Any]:
        contact_ids = params.get("contact_ids")

        if not contact_ids:
            raise ValueError("contact_ids is required")

        cid_start = min(contact_ids)
        cid_end = max(contact_ids)

        logger.info(f"Generating campaign for CID range {cid_start}–{cid_end}")

        profile = self.data_engine.get_user_group_profile(cid_start, cid_end)
        formatted_profile = self._format_user_profile(profile)

        df = self.data_engine.get_campaign_performance().collect()
        if df.is_empty():
            raise RuntimeError("No campaign history found")

        df = df.sort("success_rate", descending=True).head(10)

        campaign_history = "\n\n---\n\n".join(
            f"""
    Campaign Message:
    {row['msg_content']}

    Observed Success Rate:
    {round(row['success_rate'] * 100, 2)}%
    """
            for row in df.iter_rows(named=True)
        )

        result: BrandVoiceOutput = self.chain.invoke(
            {
                "campaign_history": campaign_history,
                "user_profile": formatted_profile,
            }
        )

        return result

    # --------------------------------------------------------------
    # HELPERS
    # --------------------------------------------------------------
    def _format_user_profile(self, profile: Dict[str, Any]) -> str:
        return "\n".join(f"{k}: {v}" for k, v in profile.items())
