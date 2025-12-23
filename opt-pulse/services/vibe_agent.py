import os
import logging
from dotenv import load_dotenv
from typing import Dict, Any, List

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


class VibeProfilerOutput(BaseModel):
    shopping_persona: str = Field(description="A descriptive shopping persona (e.g., 'Family Man', 'Green Flag')")
    behavioral_metrics: Dict[str, float] = Field(description="Key behavioral metrics (e.g., 'avg_order_value', 'visit_frequency')")
    purchase_metrics: Dict[str, float] = Field(description="Key purchase metrics (e.g., 'fashion_spend_ratio', 'tech_affinity')")
    color_palette_hints: List[str] = Field(description="A list of suggested color palette hints (e.g., ['#FF5733', '#C70039'])")


class VibeAgent:
    """
    Specialized Agent for generating customer vibe reports.
    
    This agent analyzes transaction history to create personalized shopping personas,
    behavioral insights, and shareable vibe cards.
    """
    
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        
        self.llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o", temperature=0.2)
        self.parser = JsonOutputParser(pydantic_object=VibeProfilerOutput)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert retail analyst specializing in customer persona generation.
            
Your task is to analyze transaction data and create a comprehensive customer profile including:
1. A catchy shopping persona (e.g., 'Eco Warrior', 'Tech Enthusiast', 'Bargain Hunter')
2. Behavioral metrics (frequency, recency, consistency)
3. Purchase metrics (category preferences, price sensitivity, brand loyalty)
4. Color palette hints that match the customer's vibe (hex codes)

Be creative with personas but ground them in the data. Make insights actionable."""),
            ("human", "Analyze this 12-month transaction summary:\n{transaction_summary}\n\n{format_instructions}"),
        ]).partial(format_instructions=self.parser.get_format_instructions())
        
        self.chain = self.prompt | self.llm | self.parser
    
    def process(self, params: Dict[str, Any], image_service=None, data_engine=None) -> Dict[str, Any]:
        """
        Process a vibe report request.
        
        Args:
            params: Dictionary with 'user_id' key
            image_service: ImageService instance for generating vibe cards
            data_engine: DataEngine instance for fetching transaction data
            
        Returns:
            Dictionary with vibe report results
        """
        try:
            user_id = params.get("user_id")
            if not user_id:
                raise ValueError("user_id is required for vibe report generation")
            
            logger.info(f"Vibe Agent processing request for user: {user_id}")
            
            # Fetch transaction data
            if data_engine:
                transaction_history_lf = data_engine.get_transaction_history(user_id)
                transaction_data = transaction_history_lf.collect()
                
                # Create summary for AI
                transaction_summary = f"""
User {user_id} Transaction Summary:
- Total transactions: {transaction_data.shape[0]}
- Transaction details: (aggregation logic to be implemented)
                """
            else:
                # Fallback if no data engine
                transaction_summary = f"User {user_id} has limited transaction history available."
            
            # Generate vibe profile using AI
            logger.info("Calling AI for Vibe Profile...")
            ai_output = self.chain.invoke({"transaction_summary": transaction_summary})
            logger.info("Vibe Profile generated successfully.")
            
            # Generate vibe card image if image service is available
            vibe_card_path = None
            if image_service:
                stats_for_card = {
                    "persona": ai_output.shopping_persona,
                    **ai_output.behavioral_metrics,
                    **ai_output.purchase_metrics,
                    "colors": ", ".join(ai_output.color_palette_hints)
                }
                vibe_card_path = image_service.generate_vibe_card(
                    username=user_id,
                    vibe_label=ai_output.shopping_persona,
                    stats=stats_for_card
                )
                logger.info(f"Vibe card generated at: {vibe_card_path}")
            
            return {
                "user_id": user_id,
                "shopping_persona": ai_output.shopping_persona,
                "behavioral_metrics": ai_output.behavioral_metrics,
                "purchase_metrics": ai_output.purchase_metrics,
                "color_palette_hints": ai_output.color_palette_hints,
                "vibe_card_path": vibe_card_path
            }
            
        except Exception as e:
            logger.error(f"Error in Vibe Agent processing: {e}", exc_info=True)
            raise


# Example usage
if __name__ == "__main__":
    vibe_agent = VibeAgent()
    
    test_params = {
        "user_id": "user12345"
    }
    
    try:
        result = vibe_agent.process(test_params)
        print("\nVibe Report Result:")
        import json
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")