import os
import logging
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional

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


class SmartReceiptRecommenderOutput(BaseModel):
    next_best_item: Optional[str] = Field(description="Name of the next best item to recommend, or None if no recommendation")
    loyalty_incentive_text: str = Field(description="Text for a loyalty incentive (e.g., 'Earn double points on your next purchase!')")
    coupons: List[str] = Field(description="A list of coupon codes or descriptions for the recommended item/loyalty incentive")
    recommendation_reasoning: str = Field(description="Brief explanation of why these recommendations were made")


class SmartReceiptAgent:
    """
    Specialized Agent for smart receipt recommendations.
    
    This agent analyzes current basket items and past purchase patterns to provide
    personalized product recommendations, loyalty incentives, and relevant coupons.
    """
    
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        
        self.llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o", temperature=0.3)
        self.parser = JsonOutputParser(pydantic_object=SmartReceiptRecommenderOutput)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an AI retail recommendation specialist focused on maximizing customer value.

Your task is to analyze the customer's current basket and purchase history to provide:
1. Next Best Item - A single highly relevant product recommendation
2. Loyalty Incentive - Personalized text encouraging repeat purchases
3. Coupons - Relevant discount codes or promotional offers
4. Reasoning - Brief explanation for your recommendations

Guidelines:
- Recommendations should be complementary to basket items
- Consider past purchase patterns for personalization
- Make incentives feel exclusive and time-sensitive
- Keep recommendations actionable and specific
- Focus on increasing basket value while providing genuine value to customer"""),
            ("human", """Current basket items:
{current_basket_items}

Past purchase patterns:
{past_purchase_patterns}

{format_instructions}"""),
        ]).partial(format_instructions=self.parser.get_format_instructions())
        
        self.chain = self.prompt | self.llm | self.parser
    
    def process(self, params: Dict[str, Any], data_engine=None) -> Dict[str, Any]:
        """
        Process a smart receipt recommendation request.
        
        Args:
            params: Dictionary with 'user_id' and 'current_basket_items' keys
            data_engine: DataEngine instance for fetching purchase history
            
        Returns:
            Dictionary with recommendation results
        """
        try:
            user_id = params.get("user_id")
            current_basket_items = params.get("current_basket_items", [])
            
            if not user_id:
                raise ValueError("user_id is required for smart receipt recommendations")
            
            logger.info(f"Smart Receipt Agent processing for user: {user_id}")
            
            # Format current basket items
            if isinstance(current_basket_items, list):
                if len(current_basket_items) > 0 and isinstance(current_basket_items[0], dict):
                    # List of dicts with item details
                    basket_str = "\n".join([
                        f"- {item.get('item_name', 'Unknown')} x{item.get('quantity', 1)} (${item.get('price', 0.0)})"
                        for item in current_basket_items
                    ])
                else:
                    # Simple list of item names
                    basket_str = "\n".join([f"- {item}" for item in current_basket_items])
            else:
                basket_str = str(current_basket_items)
            
            # Fetch past purchase patterns
            if data_engine:
                past_transactions_lf = data_engine.get_enriched_sales(user_id)
                past_transactions = past_transactions_lf.collect()
                
                # Create summary of past purchases
                past_patterns_str = f"""
User {user_id} Purchase History:
- Total past orders: {past_transactions.shape[0]}
- (Detailed aggregation of categories, frequencies, and preferences to be implemented)
                """
            else:
                past_patterns_str = f"Limited purchase history available for user {user_id}."
            
            # Generate recommendations using AI
            logger.info("Calling AI for Smart Receipt Recommendations...")
            raw_output = self.chain.invoke({
                   "current_basket_items": basket_str,
                   "past_purchase_patterns": past_patterns_str
            })

            ai_output = SmartReceiptRecommenderOutput(**raw_output)
            logger.info("Smart Receipt Recommendations generated successfully.")
            
            # Format next_best_item as a product object if available
            next_best_item_obj = None
            if ai_output.next_best_item:
                next_best_item_obj = {
                    "item_id": "rec_" + ai_output.next_best_item.lower().replace(" ", "_"),
                    "item_name": ai_output.next_best_item,
                    "price": 0.0,  # Would be looked up from product catalog
                    "quantity": 1
                }
            
            return {
                "user_id": user_id,
                "next_best_item": next_best_item_obj,
                "loyalty_incentive_text": ai_output.loyalty_incentive_text,
                "coupons": ai_output.coupons,
                "recommendation_reasoning": ai_output.recommendation_reasoning,
                "basket_items_count": len(current_basket_items) if isinstance(current_basket_items, list) else 0
            }
            
        except Exception as e:
            logger.error(f"Error in Smart Receipt Agent processing: {e}", exc_info=True)
            raise


# Example usage
if __name__ == "__main__":
    smart_receipt_agent = SmartReceiptAgent()
    
    test_params = {
        "user_id": "user789",
        "current_basket_items": [
            {"item_name": "Organic Coffee Beans", "quantity": 1, "price": 15.0},
            {"item_name": "Almond Milk", "quantity": 2, "price": 4.0}
        ]
    }
    
    try:
        result = smart_receipt_agent.process(test_params)
        print("\nSmart Receipt Recommendation Result:")
        import json
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")