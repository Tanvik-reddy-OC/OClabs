import logging
import os
from typing import Dict, Any

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

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
    version="0.3.0",
)

# Add CORS middleware for Streamlit compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Dependency Injection
# ------------------------------------------------------------------
def get_triage_agent() -> TriageAgent:
    """Provide TriageAgent instance."""
    return TriageAgent()


def get_vibe_agent() -> VibeAgent:
    """Provide VibeAgent instance."""
    return VibeAgent()


def get_brand_voice_agent():
    return BrandVoiceAgent()



def get_smart_receipt_agent() -> SmartReceiptAgent:
    """Provide SmartReceiptAgent instance."""
    return SmartReceiptAgent()


def get_image_service() -> ImageService:
    """Provide ImageService instance."""
    return ImageService()


def get_data_engine() -> DataEngine:
    """Provide DataEngine instance."""
    return DataEngine()


# ------------------------------------------------------------------
# Health Check
# ------------------------------------------------------------------
@app.get("/", summary="Health Check")
async def root():
    """Health check endpoint."""
    return {
        "message": "Optic Pulse API is running 🚀",
        "version": "0.3.0",
        "status": "operational"
    }


@app.get("/health", summary="Detailed Health Check")
async def health_check():
    """Detailed health check with service status."""
    return {
        "status": "healthy",
        "services": {
            "triage_agent": "ready",
            "vibe_agent": "ready",
            "brand_voice_agent": "ready",
            "smart_receipt_agent": "ready",
            "image_service": "ready",
            "data_engine": "ready"
        }
    }


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
    Universal endpoint for processing requests via intelligent triage.

    Accepts BOTH:
    1️⃣ Full triage request:
       {
         "query": "Generate a vibe report",
         "user_id": "contact123"
       }

    2️⃣ Simple request (fallback supported):
       {
         "user_id": "contact123"
       }
    """

    logger.info(f"📨 Incoming request: {request}")

    try:
        # ============================================================
        # 🔁 CHECK: If agent_type is explicitly provided, use it
        # ============================================================
        if "agent_type" in request:
            logger.info(f"✅ Agent type explicitly specified: {request['agent_type']}")
            agent_type = request["agent_type"]
            extracted_params = {k: v for k, v in request.items() if k != "agent_type"}
            triage_confidence = 1.0
            triage_result = {
                "agent_type": agent_type,
                "extracted_params": extracted_params,
                "confidence": triage_confidence,
                "reasoning": "Agent type explicitly specified by frontend"
            }
            logger.info("⏭️ Skipping triage, using explicit agent_type")
        else:
            # ============================================================
            # 🔁 FALLBACK: Add default query if missing
            # ============================================================
            if "query" not in request and "user_id" in request:
                request["query"] = "Generate a vibe report for this customer"
                logger.info("⚙️ Query missing → defaulting to vibe_report")

            # ============================================================
            # Step 1: Triage the request
            # ============================================================
            logger.info("🔄 Step 1: Classifying request with Triage Agent...")
            triage_result = triage_agent.classify_request(request)

        agent_type = triage_result["agent_type"]
        extracted_params = triage_result.get("extracted_params", {})
        triage_confidence = triage_result.get("confidence", 1.0)

        # Ensure user_id is never lost
        if "user_id" in request and "user_id" not in extracted_params:
            extracted_params["user_id"] = request["user_id"]

        logger.info(f"✅ Agent selected: {agent_type} (confidence: {triage_confidence})")
        logger.info(f"📋 Final params: {extracted_params}")

        # ============================================================
        # Step 2: Route to appropriate agent
        # ============================================================
        logger.info(f"🎯 Step 2: Routing to {agent_type} agent...")
        
        if agent_type == "vibe_report":
            logger.info("📊 Processing as Vibe Report...")
            result = vibe_agent.process(
                extracted_params,
                image_service=image_service,
                data_engine=data_engine
            )

        elif agent_type == "brand_voice":
            logger.info("✍️ Processing as Brand Voice...")
            extracted_params["contact_ids"] = request["contact_ids"]

            result = brand_voice_agent.process(extracted_params)
            logger.info(f"Brand Voice result: {result}")


        elif agent_type == "smart_receipt":
            logger.info("🛍️ Processing as Smart Receipt...")
            result = smart_receipt_agent.process(
                extracted_params,
                data_engine=data_engine
            )

        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

        # ============================================================
        # Step 3: Return unified response
        # ============================================================
        logger.info("✅ Processing complete. Returning response...")
        
        response = {
            "success": True,
            "agent_type": agent_type,
            "result": result,
            "triage_confidence": triage_confidence,
            "message": f"Request processed by {agent_type} agent"
        }
        
        logger.info(f"📤 Response ready: {response}")
        return response

    except ValueError as e:
        logger.error(f"❌ Validation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        logger.error(f"❌ Unhandled server error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# ------------------------------------------------------------------
# Static Image Serving (Vibe Cards)
# ------------------------------------------------------------------
@app.get("/static/{filename}", summary="Serve generated images")
async def serve_static_files(filename: str):
    """Serve generated vibe card images from static directory."""
    logger.info(f"📂 Serving static file: {filename}")
    
    file_path = os.path.join(STATIC_DIR, filename)

    if not os.path.exists(file_path):
        logger.warning(f"❌ File not found: {file_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Determine media type based on extension
    media_type = "image/png"
    if filename.endswith((".jpg", ".jpeg")):
        media_type = "image/jpeg"
    elif filename.endswith(".gif"):
        media_type = "image/gif"

    logger.info(f"✅ Serving {filename} as {media_type}")
    return FileResponse(file_path, media_type=media_type)


# ------------------------------------------------------------------
# Info endpoints
# ------------------------------------------------------------------
@app.get("/info", summary="API Information")
async def api_info():
    """Get API information and available agents."""
    return {
        "api_name": "Optic Pulse API",
        "version": "0.3.0",
        "available_agents": [
            {
                "name": "vibe_report",
                "description": "Generates customer shopping personas and vibes",
                "required_params": ["user_id"]
            },
            {
                "name": "brand_voice",
                "description": "Clones brand voice and generates campaigns",
                "required_params": ["campaign_texts"]
            },
            {
                "name": "smart_receipt",
                "description": "Provides personalized product recommendations",
                "required_params": ["user_id", "current_basket_items"]
            }
        ],
        "endpoints": {
            "process": "/process",
            "static": "/static/{filename}",
            "health": "/health",
            "info": "/info"
        }
    }


# ------------------------------------------------------------------
# Error handling
# ------------------------------------------------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    logger.error(f"HTTP Exception: {exc.detail}")
    return {
        "success": False,
        "error": exc.detail,
        "status_code": exc.status_code
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting Optic Pulse API...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )