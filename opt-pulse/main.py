import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import FileResponse
from typing import Dict, Any
import os

from services.triage_agent import TriageAgent
from services.vibe_agent import VibeAgent
from services.brand_voice_agent import BrandVoiceAgent
from services.smart_receipt_agent import SmartReceiptAgent
from services.image_service import ImageService, STATIC_DIR
from services.data_engine import DataEngine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Optic Pulse API",
    description="Modular AI-retail suite for OptCulture with Triage Agent",
    version="0.2.0",
)

# --- Dependency Injection for Services ---
def get_triage_agent() -> TriageAgent:
    return TriageAgent()

def get_vibe_agent() -> VibeAgent:
    return VibeAgent()

def get_brand_voice_agent() -> BrandVoiceAgent:
    return BrandVoiceAgent()

def get_smart_receipt_agent() -> SmartReceiptAgent:
    return SmartReceiptAgent()

def get_image_service() -> ImageService:
    return ImageService()

def get_data_engine() -> DataEngine:
    return DataEngine()

# --- Root Endpoint ---
@app.get("/", summary="Health Check")
async def root():
    return {"message": "Optic Pulse API with Triage Agent is running!"}

# --- Single Unified Endpoint with Triage Agent ---
@app.post(
    "/process", 
    summary="Process Request with Triage Agent"
)
async def process_request(
    request: Dict[Any, Any],
    triage_agent: TriageAgent = Depends(get_triage_agent),
    vibe_agent: VibeAgent = Depends(get_vibe_agent),
    brand_voice_agent: BrandVoiceAgent = Depends(get_brand_voice_agent),
    smart_receipt_agent: SmartReceiptAgent = Depends(get_smart_receipt_agent),
    image_service: ImageService = Depends(get_image_service),
    data_engine: DataEngine = Depends(get_data_engine)
):
    """
    Universal endpoint that uses a Triage Agent to route requests to the appropriate specialized agent.
    
    Expected request format:
    {
        "query": "User's natural language request",
        "user_id": "optional user identifier",
        "data": {
            "any additional context or data"
        }
    }
    """
    logger.info(f"Received request: {request}")
    
    try:
        # Step 1: Triage Agent determines which specialized agent to use
        triage_result = triage_agent.classify_request(request)
        agent_type = triage_result["agent_type"]
        extracted_params = triage_result["extracted_params"]
        
        logger.info(f"Triage Agent routed to: {agent_type}")
        logger.info(f"Extracted parameters: {extracted_params}")
        
        # Step 2: Route to the appropriate specialized agent
        if agent_type == "vibe_report":
            result = vibe_agent.process(
                extracted_params, 
                image_service=image_service, 
                data_engine=data_engine
            )
            
        elif agent_type == "brand_voice":
            result = brand_voice_agent.process(extracted_params)
            
        elif agent_type == "smart_receipt":
            result = smart_receipt_agent.process(
                extracted_params, 
                data_engine=data_engine
            )
            
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        # Step 3: Return unified response
        return {
            "agent_type": agent_type,
            "result": result,
            "triage_confidence": triage_result.get("confidence", 1.0)
        }
        
    except ValueError as e:
        logger.error(f"Validation error in /process: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Internal server error during request processing."
        )


@app.get("/static/{filename}", summary="Serve Static Files")
async def serve_static_files(filename: str):
    """
    Serves static files, primarily for retrieving generated Vibe Cards.
    """
    file_path = os.path.join(STATIC_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    
    media_type = "image/png"
    if filename.endswith(".jpg") or filename.endswith(".jpeg"):
        media_type = "image/jpeg"
    elif filename.endswith(".gif"):
        media_type = "image/gif"
    
    return FileResponse(file_path, media_type=media_type)