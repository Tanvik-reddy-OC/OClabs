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
# OUTPUT SCHEMA
# ------------------------------------------------------------------
class BrandVoiceAgent(BaseModel):
    new_campaign_body: str = Field(description="Generated campaign body text")
    predicted_success_score: int = Field(
        description="Predicted success score (0–100)",
        ge=0,
        le=100
    )
    inferred_patterns: Dict[str, str] = Field(
        description="Patterns learned from historical campaigns"
    )

# ------------------------------------------------------------------
# LLM SERVICE
# ------------------------------------------------------------------
class BrandVoiceLLMService:
    """
    Builds data-driven campaign content using:
    - templates
    - campaign_metrics
    - aggregated user group profile (CID range)
    """

    def __init__(self):
        self.data_engine = DataEngine()

        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.25,
            api_key=OPENAI_API_KEY
        )

        self.parser = JsonOutputParser(
            pydantic_object=BrandVoiceAgent
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
You are a senior marketing intelligence AI.

You are given historical campaign messages with their real-world success rates,
and a summarized user group profile.

Your task:
1. Identify patterns in HIGH vs LOW performing campaigns
2. Infer brand voice (tone, urgency, emoji usage, CTA style)
3. Generate a NEW campaign body optimized for this user group
4. Predict the success score (0–100)

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
                )
            ]
        ).partial(
            format_instructions=self.parser.get_format_instructions()
        )

        self.chain = self.prompt | self.llm | self.parser

    # ------------------------------------------------------------------
    # CORE ENTRY POINT
    # ------------------------------------------------------------------
    def generate_campaign(
        self,
        cid_start: int,
        cid_end: int
    ) -> Dict[str, Any]:
        """
        Generate a campaign using historical performance
        and an aggregated user group profile.
        """
        logger.info(
            f"Generating campaign for CID range {cid_start}–{cid_end}"
        )

        # 1. Build user group profile
        profile = self.data_engine.get_user_group_profile(
            cid_start,
            cid_end
        )
        formatted_profile = self._format_user_profile(profile)

        # 2. Fetch campaign performance
        lf = self.data_engine.get_campaign_performance()
        df = lf.collect()

        if df.is_empty():
            raise RuntimeError("No campaign history found")

        # 3. Use top-performing campaigns as learning signal
        df = df.sort("success_rate", descending=True).head(10)

        campaign_blocks = []
        for row in df.iter_rows(named=True):
            campaign_blocks.append(
                f"""
Campaign Message:
{row['msg_content']}

Observed Success Rate:
{round(row['success_rate'] * 100, 2)}%
"""
            )

        campaign_history = "\n\n---\n\n".join(campaign_blocks)

        # 4. Call LLM
        logger.info("Invoking LLM for brand voice generation...")

        result = self.chain.invoke(
            {
                "campaign_history": campaign_history,
                "user_profile": formatted_profile
            }
        )

        logger.info("Campaign generation successful")
        logger.debug(f"LLM Output: {result}")

        return result

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------
    def _format_user_profile(
        self,
        profile: Dict[str, Any]
    ) -> str:
        """
        Converts aggregated user stats into LLM-readable text.
        """
        lines = []
        for key, value in profile.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)

# ------------------------------------------------------------------
# LOCAL TEST
# ------------------------------------------------------------------
if __name__ == "__main__":
    service = BrandVoiceLLMService()

    output = service.generate_campaign(
        cid_start=20186123,
        cid_end=20186128
    )

    import json
    print(json.dumps(output, indent=2))
