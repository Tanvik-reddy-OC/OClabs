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


class BrandVoiceClonerOutput(BaseModel):
    new_campaign_body: str = Field(description="The generated new campaign text")
    predicted_success_score: int = Field(description="Predicted success score of the campaign (0-100)", ge=0, le=100)
    voice_characteristics: Dict[str, str] = Field(description="Identified brand voice characteristics")


class BrandVoiceAgent:
    """
    Specialized Agent for brand voice cloning and campaign generation.
    
    This agent analyzes past marketing campaigns to extract brand voice patterns
    and generates new campaigns that match the identified style.
    """
    
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        
        self.llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o", temperature=0.2)
        self.parser = JsonOutputParser(pydantic_object=BrandVoiceClonerOutput)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a marketing expert specialized in brand voice analysis and campaign creation.

Your task is to:
1. Analyze the provided campaign texts to identify key brand voice characteristics:
   - Tone (formal, casual, playful, urgent, etc.)
   - Emoji density and style
   - Call-to-action patterns
   - Sentence structure and length
   - Target audience indicators
2. Generate a new campaign that matches this identified voice
3. Predict how successful this campaign will be (0-100 score)
4. Document the voice characteristics you identified

Be consistent with the brand's established patterns while keeping content fresh."""),
            ("human", "Analyze these past campaign texts and generate a new campaign:\n\n{campaign_texts}\n\n{format_instructions}"),
        ]).partial(format_instructions=self.parser.get_format_instructions())
        
        self.chain = self.prompt | self.llm | self.parser
    
    def process(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a brand voice cloning request.
        
        Args:
            params: Dictionary with 'campaign_texts' key containing list of past campaigns
            
        Returns:
            Dictionary with new campaign and analysis results
        """
        try:
            campaign_texts = params.get("campaign_texts", [])
            if not campaign_texts:
                raise ValueError("campaign_texts list is required for brand voice cloning")
            
            if not isinstance(campaign_texts, list):
                raise ValueError("campaign_texts must be a list of strings")
            
            logger.info(f"Brand Voice Agent processing {len(campaign_texts)} campaign texts...")
            
            # Format campaign texts for AI
            formatted_campaigns = "\n\n---\n\n".join([
                f"Campaign {i+1}:\n{text}" 
                for i, text in enumerate(campaign_texts)
            ])
            
            # Generate brand voice clone using AI
            logger.info("Calling AI for Brand Voice Clone...")
            ai_output = self.chain.invoke({"campaign_texts": formatted_campaigns})
            logger.info("Brand Voice Clone generated successfully.")
            
            return {
                "new_campaign_body": ai_output.new_campaign_body,
                "predicted_success_score": ai_output.predicted_success_score,
                "voice_characteristics": ai_output.voice_characteristics,
                "campaigns_analyzed": len(campaign_texts)
            }
            
        except Exception as e:
            logger.error(f"Error in Brand Voice Agent processing: {e}", exc_info=True)
            raise


# Example usage
if __name__ == "__main__":
    brand_voice_agent = BrandVoiceAgent()
    
    test_params = {
        "campaign_texts": [
            "Hey VIP! ✨ Your exclusive offer is here! Shop now & get 20% off! Limited time! 🚀 #VIP #Sale",
            "Don't miss out! Our new collection just dropped! 🔥 Click to explore! 👉 [Link]",
            "Treat yourself! You deserve it. Use code SAVE15 at checkout! 🛍️ T&Cs apply.",
            "Flash Sale Alert! 🚨 50% off selected items! Hurry, while stocks last! ⏰",
            "Weekend Vibes! 🌟 Refresh your wardrobe with our latest arrivals. Shop now! 💫"
        ]
    }
    
    try:
        result = brand_voice_agent.process(test_params)
        print("\nBrand Voice Campaign Result:")
        import json
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")