import os
import logging
from dotenv import load_dotenv
from typing import List, Dict, Optional

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser


# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Pydantic Output Parsers for structured AI responses ---
class VibeProfilerOutput(BaseModel):
    shopping_persona: str = Field(description="A descriptive shopping persona (e.g., 'Family Man', 'Green Flag')")
    behavioral_metrics: Dict[str, float] = Field(description="Key behavioral metrics (e.g., 'avg_order_value', 'visit_frequency')")
    purchase_metrics: Dict[str, float] = Field(description="Key purchase metrics (e.g., 'fashion_spend_ratio', 'tech_affinity')")
    color_palette_hints: List[str] = Field(description="A list of suggested color palette hints (e.g., ['#FF5733', '#C70039'])")

class BrandVoiceClonerOutput(BaseModel):
    new_campaign_body: str = Field(description="The generated new campaign text")
    predicted_success_score: int = Field(description="Predicted success score of the campaign (0-100)", ge=0, le=100)

class SmartReceiptRecommenderOutput(BaseModel):
    next_best_item: Optional[str] = Field(description="Name of the next best item to recommend, or None if no recommendation")
    loyalty_incentive_text: str = Field(description="Text for a loyalty incentive (e.g., 'Earn double points on your next purchase!')")
    coupons: List[str] = Field(description="A list of coupon codes or descriptions for the recommended item/loyalty incentive")

class AIService:
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        
        self.llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o", temperature=0.2) # Low temperature for determinism
        
        # Initialize output parsers
        self.vibe_profiler_parser = JsonOutputParser(pydantic_object=VibeProfilerOutput)
        self.brand_voice_cloner_parser = JsonOutputParser(pydantic_object=BrandVoiceClonerOutput)
        self.smart_receipt_recommender_parser = JsonOutputParser(pydantic_object=SmartReceiptRecommenderOutput)

        # 1. Vibe Profiler Prompt
        self.vibe_profiler_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are an expert retail analyst. Analyze the provided transaction summary and generate a customer shopping persona, key metrics, and color palette hints. Output in JSON format."),
                ("human", "Analyze this 12-month transaction summary:\n{transaction_summary}\n\n{format_instructions}"),
            ]
        ).partial(format_instructions=self.vibe_profiler_parser.get_format_instructions())

        # 2. Brand Voice Cloner Prompt
        self.brand_voice_cloner_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a marketing expert specialized in brand voice cloning. Analyze the given campaign texts to extract tone, emoji density, CTA style, and body style. Then, generate a new campaign body based on these insights and predict its success score (0-100). Output in JSON format."),
                ("human", "Here are 10 past campaign texts:\n{campaign_texts}\n\n{format_instructions}"),
            ]
        ).partial(format_instructions=self.brand_voice_cloner_parser.get_format_instructions())

        # 3. Smart Receipt Recommender Prompt
        self.smart_receipt_recommender_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are an AI assistant for personalized retail recommendations. Given current basket items and past purchase patterns, suggest the next best item, a loyalty incentive, and relevant coupons. Output in JSON format."),
                ("human", "Current basket items:\n{current_basket_items}\n\nPast purchase patterns:\n{past_purchase_patterns}\n\n{format_instructions}"),
            ]
        ).partial(format_instructions=self.smart_receipt_recommender_parser.get_format_instructions())

        self.vibe_profiler_chain = self.vibe_profiler_prompt | self.llm | self.vibe_profiler_parser
        self.brand_voice_cloner_chain = self.brand_voice_cloner_prompt | self.llm | self.brand_voice_cloner_parser
        self.smart_receipt_recommender_chain = self.smart_receipt_recommender_prompt | self.llm | self.smart_receipt_recommender_parser

    def get_vibe_report(self, transaction_summary: str) -> VibeProfilerOutput:
        """Generates a vibe report based on transaction summary."""
        try:
            logger.info("Calling AI for Vibe Report...")
            response = self.vibe_profiler_chain.invoke({"transaction_summary": transaction_summary})
            logger.info("Vibe Report AI call successful.")
            return response
        except Exception as e:
            logger.error(f"Error in get_vibe_report: {e}", exc_info=True)
            raise

    def get_brand_voice_clone(self, campaign_texts: List[str]) -> BrandVoiceClonerOutput:
        """Clones brand voice and generates a new campaign."""
        try:
            logger.info("Calling AI for Brand Voice Clone...")
            # Langchain expects string for 'human' message, so join list of texts
            response = self.brand_voice_cloner_chain.invoke({"campaign_texts": "\n".join(campaign_texts)})
            logger.info("Brand Voice Clone AI call successful.")
            return response
        except Exception as e:
            logger.error(f"Error in get_brand_voice_clone: {e}", exc_info=True)
            raise

    def get_smart_receipt_recommendations(self, current_basket_items: str, past_purchase_patterns: str) -> SmartReceiptRecommenderOutput:
        """Generates smart receipt recommendations."""
        try:
            logger.info("Calling AI for Smart Receipt Recommendations...")
            response = self.smart_receipt_recommender_chain.invoke({
                "current_basket_items": current_basket_items, 
                "past_purchase_patterns": past_purchase_patterns
            })
            logger.info("Smart Receipt Recommendations AI call successful.")
            return response
        except Exception as e:
            logger.error(f"Error in get_smart_receipt_recommendations: {e}", exc_info=True)
            raise

# Example usage (for testing, not for production direct execution)
if __name__ == "__main__":
    ai_service = AIService()

    # Test Vibe Profiler
    sample_transaction_summary = """
    User bought mostly eco-friendly products, organic food, and sustainable fashion in the last year.
    Total spend: $1500. Average order value: $75.
    Categories: 40% groceries, 30% apparel, 20% home goods, 10% other.
    """
    try:
        vibe_report = ai_service.get_vibe_report(sample_transaction_summary)
        print("\nVibe Report:")
        print(vibe_report.model_dump_json(indent=2))
    except Exception as e:
        print(f"Failed to get vibe report: {e}")

    # Test Brand Voice Cloner
    sample_campaign_texts = [
        "Hey VIP! ✨ Your exclusive offer is here! Shop now & get 20% off! Limited time! 🚀 #VIP #Sale",
        "Don't miss out! Our new collection just dropped! 🔥 Click to explore! 👉 [Link]",
        "Treat yourself! You deserve it. Use code SAVE15 at checkout! 🛍️ T&Cs apply."
    ]
    try:
        brand_voice = ai_service.get_brand_voice_clone(sample_campaign_texts)
        print("\nBrand Voice Clone:")
        print(brand_voice.model_dump_json(indent=2))
    except Exception as e:
        print(f"Failed to get brand voice clone: {e}")

    # Test Smart Receipt Recommender
    sample_current_basket = """
    - Organic Coffee Beans x1 ($15)
    - Almond Milk x2 ($8)
    """
    sample_past_patterns = """
    User frequently buys breakfast items, subscribes to healthy eating blogs,
    and has previously purchased vegan protein powder and reusable coffee cups.
    """
    try:
        smart_receipt = ai_service.get_smart_receipt_recommendations(
            sample_current_basket, sample_past_patterns
        )
        print("\nSmart Receipt Recommendations:")
        print(smart_receipt.model_dump_json(indent=2))
    except Exception as e:
        print(f"Failed to get smart receipt recommendations: {e}")
