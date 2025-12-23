from pydantic import BaseModel
from typing import List, Dict, Optional

# --- Vibe Report Models ---
class VibeReportRequest(BaseModel):
    user_id: str
    # Assuming transaction summary will be fetched internally by the service
    # based on user_id, or passed in a more structured way if needed.
    # For now, keeping it simple as user_id.

class VibeReportResponse(BaseModel):
    user_id: str
    shopping_persona: str
    behavioral_metrics: Dict[str, float]
    purchase_metrics: Dict[str, float]
    color_palette_hints: List[str]
    vibe_card_path: str # Path to the generated image

# --- Brand Voice Cloner Models ---
class BrandVoiceClonerRequest(BaseModel):
    campaign_texts: List[str]

class BrandVoiceClonerResponse(BaseModel):
    new_campaign_body: str
    predicted_success_score: float # 0-100

# --- Smart Receipts Models ---
class ProductItem(BaseModel):
    item_id: str
    item_name: str
    price: float
    quantity: int

class SmartReceiptRecommenderRequest(BaseModel):
    user_id: str
    current_basket_items: List[ProductItem]
    # Assuming past purchase patterns will be fetched internally by the service
    # based on user_id.

class SmartReceiptRecommenderResponse(BaseModel):
    next_best_item: Optional[ProductItem] = None # Optional in case no recommendation
    loyalty_incentive_text: str
    coupons: List[str] # List of coupon codes or descriptions
