import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import FileResponse
from typing import List, Dict, Any

from services.ai_service import AIService, VibeProfilerOutput, BrandVoiceClonerOutput, SmartReceiptRecommenderOutput
from services.image_service import ImageService, STATIC_DIR
from services.data_engine import DataEngine
from schemas.models import (
    VibeReportRequest, VibeReportResponse,
    BrandVoiceClonerRequest, BrandVoiceClonerResponse,
    SmartReceiptRecommenderRequest, SmartReceiptRecommenderResponse,
    ProductItem
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Optic Pulse API",
    description="Modular AI-retail suite for OptCulture",
    version="0.1.0",
)

# --- Dependency Injection for Services ---
def get_ai_service() -> AIService:
    return AIService()

def get_image_service() -> ImageService:
    return ImageService()

def get_data_engine() -> DataEngine:
    return DataEngine()

# --- Root Endpoint ---
@app.get("/", summary="Health Check")
async def root():
    return {"message": "Optic Pulse API is running!"}

# --- API Endpoints ---

@app.post(
    "/vibe-report", 
    response_model=VibeReportResponse,
    summary="Generate Vibe Report for a Customer"
)
async def generate_vibe_report_endpoint(
    request: VibeReportRequest,
    ai_service: AIService = Depends(get_ai_service),
    image_service: ImageService = Depends(get_image_service),
    data_engine: DataEngine = Depends(get_data_engine)
):
    """
    Generates a personalized Vibe Report for a customer based on their transaction history.
    This includes a shopping persona, key behavioral/purchase metrics, and color palette hints.
    """
    logger.info(f"Received request for Vibe Report for user_id: {request.user_id}")
    try:
        # 1. Fetch data from DataEngine
        transaction_history_lf = data_engine.get_transaction_history(request.user_id)
        # For the AI prompt, we need a summarized string. This is a simplification.
        # In a real scenario, this would involve complex Polars aggregations.
        # For now, let's just indicate the data was fetched.
        # This will be refined to provide a meaningful summary to the AI.
        
        # Simulating a transaction summary for the AI for now
        # TODO: Implement robust Polars aggregation to create a summary string
        # For now, let's create a dummy summary based on the LF schema
        # In a real app, you'd collect() and process here, but we aim for lazy if possible
        # For LLM input, a string is best.
        
        # Example: Just count transactions for now, or fetch a sample
        transaction_summary_str = f"User {request.user_id} has {transaction_history_lf.collect().shape[0]} transactions over the last 12 months. Details: (full aggregation to be implemented)."

        # 2. Get AI Vibe Profile
        ai_output: VibeProfilerOutput = ai_service.get_vibe_report(transaction_summary_str)

        # 3. Generate Vibe Card Image
        # Convert Pydantic model to dict for image service stats
        stats_for_card = {
            "persona": ai_output.shopping_persona,
            **ai_output.behavioral_metrics,
            **ai_output.purchase_metrics,
            "colors": ", ".join(ai_output.color_palette_hints)
        }
        vibe_card_path = image_service.generate_vibe_card(
            username=request.user_id,
            vibe_label=ai_output.shopping_persona,
            stats=stats_for_card
        )

        return VibeReportResponse(
            user_id=request.user_id,
            shopping_persona=ai_output.shopping_persona,
            behavioral_metrics=ai_output.behavioral_metrics,
            purchase_metrics=ai_output.purchase_metrics,
            color_palette_hints=ai_output.color_palette_hints,
            vibe_card_path=vibe_card_path
        )
    except ValueError as e:
        logger.error(f"Validation error for /vibe-report: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating vibe report for user {request.user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during vibe report generation.")

@app.post(
    "/brand-voice",
    response_model=BrandVoiceClonerResponse,
    summary="Clone Brand Voice and Generate New Campaign"
)
async def generate_brand_voice_campaign_endpoint(
    request: BrandVoiceClonerRequest,
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Analyzes past campaign texts to clone brand voice and generates a new campaign body
    with a predicted success score.
    """
    logger.info("Received request for Brand Voice Clone.")
    try:
        ai_output: BrandVoiceClonerOutput = ai_service.get_brand_voice_clone(request.campaign_texts)
        return BrandVoiceClonerResponse(
            new_campaign_body=ai_output.new_campaign_body,
            predicted_success_score=ai_output.predicted_success_score
        )
    except ValueError as e:
        logger.error(f"Validation error for /brand-voice: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating brand voice campaign: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during brand voice generation.")

@app.post(
    "/smart-receipt",
    response_model=SmartReceiptRecommenderResponse,
    summary="Generate Smart Receipt Recommendations"
)
async def generate_smart_receipt_endpoint(
    request: SmartReceiptRecommenderRequest,
    ai_service: AIService = Depends(get_ai_service),
    data_engine: DataEngine = Depends(get_data_engine)
):
    """
    Generates personalized recommendations for a smart receipt, including the next best item,
    loyalty incentives, and coupons, based on current basket and past purchase patterns.
    """
    logger.info(f"Received request for Smart Receipt for user_id: {request.user_id}")
    try:
        # Fetch past purchase patterns from DataEngine
        # For simplicity, convert the list of ProductItem to a string for the AI.
        # In a real app, this would involve more sophisticated processing of `data_engine.get_transaction_history`
        # and `data_engine.get_customer_metadata` to form a rich "past purchase patterns" summary.
        past_transactions_lf = data_engine.get_transaction_history(request.user_id)
        # TODO: Aggregate past_transactions_lf into a meaningful summary string for the AI
        past_purchase_patterns_str = f"User {request.user_id} past transactions: {past_transactions_lf.collect().shape[0]} orders. (detailed summary to be implemented)"
        
        current_basket_str = "\n".join([f"- {item.item_name} x{item.quantity} (${item.price})" for item in request.current_basket_items])


        ai_output: SmartReceiptRecommenderOutput = ai_service.get_smart_receipt_recommendations(
            current_basket_items=current_basket_str,
            past_purchase_patterns=past_purchase_patterns_str
        )

        # Assuming `next_best_item` from AI is a string name, convert back to ProductItem if it exists
        next_best_item_model: Optional[ProductItem] = None
        if ai_output.next_best_item:
            # This is a simplification; ideally, we'd lookup the item details from a product catalog
            # For now, creating a dummy ProductItem with only the name
            next_best_item_model = ProductItem(item_id="rec_id", item_name=ai_output.next_best_item, price=0.0, quantity=1)


        return SmartReceiptRecommenderResponse(
            next_best_item=next_best_item_model,
            loyalty_incentive_text=ai_output.loyalty_incentive_text,
            coupons=ai_output.coupons
        )
    except ValueError as e:
        logger.error(f"Validation error for /smart-receipt: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating smart receipt for user {request.user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during smart receipt generation.")


@app.get("/static/{filename}", summary="Serve Static Files")
async def serve_static_files(filename: str):
    """
    Serves static files, primarily for retrieving generated Vibe Cards.
    """
    file_path = os.path.join(STATIC_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    
    # Determine media type based on file extension
    media_type = "image/png" # Default for vibe cards
    if filename.endswith(".jpg") or filename.endswith(".jpeg"):
        media_type = "image/jpeg"
    elif filename.endswith(".gif"):
        media_type = "image/gif"
    
    return FileResponse(file_path, media_type=media_type)
