import logging
import os
from typing import Dict, Any

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import FileResponse

from services.triage_agent import TriageAgent
from services.vibe_agent import VibeAgent
from services.brand_voice_agent import BrandVoiceAgent
from services.smart_receipt_agent import SmartReceiptAgent
from services.image_service import ImageService, STATIC_DIR
from services.data_engine import DataEngine

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# FastAPI App
# ------------------------------------------------------------------
app = FastAPI(
    title="Optic Pulse API",
    description="Modular AI-retail suite for OptCulture with Triage Agent",
    version="0.2.1",
)

# ------------------------------------------------------------------
# Dependency Injection
# ------------------------------------------------------------------
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

# ------------------------------------------------------------------
# Health Check
# ------------------------------------------------------------------
@app.get("/", summary="Health Check")
async def root():
    return {"message": "Optic Pulse API is running 🚀"}

# ------------------------------------------------------------------
# Unified Agentic Endpoint
# ------------------------------------------------------------------
@app.post("/process", summary="Process request via Triage Agent")
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
    Universal endpoint.

    Accepts BOTH:
    1️⃣ Full triage request
       {
         "query": "Generate a vibe report",
         "user_id": "contact123"
       }

    2️⃣ Simple Streamlit request (fallback supported)
       {
         "user_id": "contact123"
       }
    """

    logger.info(f"Incoming request payload: {request}")

    try:
        # ------------------------------------------------------------
        # 🔁 FALLBACK FOR STREAMLIT (NO QUERY SENT)
        # ------------------------------------------------------------
        if "query" not in request and "user_id" in request:
            request["query"] = "Generate a vibe report for this customer"
            logger.info("Query missing → defaulting to vibe_report flow")

        # ------------------------------------------------------------
        # Step 1: Triage
        # ------------------------------------------------------------
        triage_result = triage_agent.classify_request(request)

        agent_type = triage_result["agent_type"]
        extracted_params = triage_result.get("extracted_params", {})

        # Ensure user_id is never lost
        if "user_id" in request and "user_id" not in extracted_params:
            extracted_params["user_id"] = request["user_id"]

        logger.info(f"Agent selected: {agent_type}")
        logger.info(f"Final params: {extracted_params}")

        # ------------------------------------------------------------
        # Step 2: Route to agent
        # ------------------------------------------------------------
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

        # ------------------------------------------------------------
        # Step 3: Unified Response
        # ------------------------------------------------------------
        return {
            "agent_type": agent_type,
            "result": result,
            "triage_confidence": triage_result.get("confidence", 1.0)
        }

    except ValueError as e:
        logger.error("Validation error", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        logger.error("Unhandled server error", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# ------------------------------------------------------------------
# Static Image Serving (Vibe Cards)
# ------------------------------------------------------------------
@app.get("/static/{filename}", summary="Serve generated images")
async def serve_static_files(filename: str):
    file_path = os.path.join(STATIC_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    media_type = "image/png"
    if filename.endswith((".jpg", ".jpeg")):
        media_type = "image/jpeg"
    elif filename.endswith(".gif"):
        media_type = "image/gif"

    return FileResponse(file_path, media_type=media_type)
