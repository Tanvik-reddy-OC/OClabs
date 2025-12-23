import os
import logging
from dotenv import load_dotenv
from typing import Dict, Any

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


class TriageOutput(BaseModel):
    agent_type: str = Field(
        description="The type of agent to route to: 'vibe_report', 'brand_voice', or 'smart_receipt'"
    )
    extracted_params: Dict[str, Any] = Field(
        description="Extracted parameters needed for the selected agent"
    )
    confidence: float = Field(
        description="Confidence score for the classification (0-1)",
        ge=0.0,
        le=1.0
    )
    reasoning: str = Field(
        description="Brief explanation of why this agent was selected"
    )


class TriageAgent:
    """
    Triage Agent that classifies incoming requests and routes them to appropriate specialized agents.
    
    Specialized Agents:
    1. Vibe Report Agent - Generates customer shopping personas and vibes
    2. Brand Voice Agent - Clones brand voice and generates campaigns
    3. Smart Receipt Agent - Provides personalized product recommendations
    """
    
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        
        self.llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o", temperature=0.1)
        self.parser = JsonOutputParser(pydantic_object=TriageOutput)
        
        # Triage classification prompt
        self.triage_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Triage Agent for an AI-retail platform. Your job is to classify incoming requests and route them to the appropriate specialized agent.

Available Agents:
1. **vibe_report** - Generates personalized customer shopping personas, behavioral metrics, and shareable vibe cards
   - Triggers: customer profile, shopping persona, customer analysis, vibe report, user behavior, purchase patterns
   - Required params: user_id
   
2. **brand_voice** - Clones brand voice from past campaigns and generates new marketing content
   - Triggers: campaign creation, marketing copy, brand voice, email content, promotional text
   - Required params: campaign_texts (list of past campaigns)
   
3. **smart_receipt** - Provides personalized product recommendations based on current basket and purchase history
   - Triggers: product recommendations, next best item, receipt suggestions, what to buy, upsell, cross-sell
   - Required params: user_id, current_basket_items

Instructions:
- Analyze the user's request and determine which agent is most appropriate
- Extract all necessary parameters from the request
- Provide a confidence score (0-1) for your classification
- Explain your reasoning briefly
- If the request is ambiguous, choose the most likely agent and note lower confidence"""),
            ("human", "Classify this request:\n\n{request_json}\n\n{format_instructions}")
        ]).partial(format_instructions=self.parser.get_format_instructions())
        
        self.triage_chain = self.triage_prompt | self.llm | self.parser
    
    def classify_request(self, request: Dict[Any, Any]) -> Dict[str, Any]:
        """
        Classifies the incoming request and determines which specialized agent should handle it.
        
        Args:
            request: Dictionary containing the user's request
            
        Returns:
            Dictionary with agent_type, extracted_params, confidence, and reasoning
        """
        try:
            logger.info("Triage Agent classifying request...")
            
            # Convert request to string representation for the LLM
            import json
            request_json = json.dumps(request, indent=2)
            
            result = self.triage_chain.invoke({"request_json": request_json})
            
            logger.info(f"Triage classification complete: {result.agent_type} (confidence: {result.confidence})")
            logger.info(f"Reasoning: {result.reasoning}")
            
            return {
                "agent_type": result.agent_type,
                "extracted_params": result.extracted_params,
                "confidence": result.confidence,
                "reasoning": result.reasoning
            }
            
        except Exception as e:
            logger.error(f"Error in Triage Agent classification: {e}", exc_info=True)
            raise


# Example usage
if __name__ == "__main__":
    triage_agent = TriageAgent()
    
    # Test cases
    test_requests = [
        {
            "query": "Generate a vibe report for user12345",
            "user_id": "user12345"
        },
        {
            "query": "Create a new marketing campaign based on these past emails",
            "data": {
                "campaign_texts": [
                    "Hey VIP! ✨ Your exclusive offer is here!",
                    "Don't miss out! Our new collection just dropped! 🔥"
                ]
            }
        },
        {
            "query": "What products should I recommend to this customer?",
            "user_id": "user789",
            "data": {
                "current_basket": ["coffee", "milk"]
            }
        }
    ]
    
    for i, test_req in enumerate(test_requests, 1):
        print(f"\n{'='*60}")
        print(f"Test Case {i}:")
        print(f"{'='*60}")
        try:
            result = triage_agent.classify_request(test_req)
            print(f"Agent Type: {result['agent_type']}")
            print(f"Confidence: {result['confidence']}")
            print(f"Reasoning: {result['reasoning']}")
            print(f"Extracted Params: {result['extracted_params']}")
        except Exception as e:
            print(f"Error: {e}")