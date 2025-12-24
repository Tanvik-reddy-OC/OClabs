import os
import logging
import requests
import base64
from io import BytesIO
from dotenv import load_dotenv
from typing import Dict, Any

# Data Processing
import polars as pl

# AI Libraries
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
from pydantic import BaseModel, Field

# Image Manipulation
from PIL import Image, ImageDraw, ImageFont

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

logger = logging.getLogger(__name__)

# --- OUTPUT SCHEMA ---
class VibeProfilerOutput(BaseModel):
    vibe_title: str = Field(description="Title like 'Weekend Warrior'")
    vibe_subtitle: str = Field(description="Short witty subtitle")
    top_category: str = Field(description="Most purchased category")
    peak_shopping_day: str = Field(description="Top shopping day")
    color_vibe: str = Field(description="Hex code")
    fun_fact: str = Field(description="Fun fact string")
    # Prompt for the BACKGROUND only
    image_prompt: str = Field(description="Prompt for DALL-E to generate a BACKGROUND image. Instruct it to leave space in the center for text. Do not ask for text.")

class VibeAgent:
    def __init__(self):
        # 1. Text Logic (Gemini Pro)
        self.llm = ChatGoogleGenerativeAI(
            google_api_key=GOOGLE_API_KEY,
            model="gemini-pro",
            temperature=0.7
        )

        # 2. Image Logic (DALL-E 3)
        try:
            self.image_gen = DallEAPIWrapper(model="dall-e-3")
        except:
            self.image_gen = None

        self.parser = JsonOutputParser(pydantic_object=VibeProfilerOutput)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a creative art director."),
            ("human", """Analyze this data and create a Vibe Profile.
             
             Context: {transaction_summary}
             
             Task:
             1. Create a Title and Stats.
             2. Create an 'image_prompt' for DALL-E. 
             IMPORTANT: The image_prompt must describe a BACKGROUND TEXTURE or SCENE (e.g., 'A retro paper texture with green leaf borders', 'A futuristic neon grid frame'). 
             Tell DALL-E to KEEP THE CENTER CLEAR/EMPTY so we can overlay text later.
             
             {format_instructions}
             """)
        ]).partial(format_instructions=self.parser.get_format_instructions())

        self.chain = self.prompt | self.llm | self.parser

    def _overlay_text_on_image(self, image_url: str, data: Dict) -> str:
        """
        Downloads the background image and draws the stats on top using Python PIL.
        Returns a Base64 string.
        """
        try:
            # 1. Download the generated background
            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content))
            
            # 2. Setup Drawing
            draw = ImageDraw.Draw(img)
            width, height = img.size
            
            # 3. Load Fonts (Try to find a system font, fallback to default)
            try:
                # Attempt to load a nice bold font (adjust path for Linux/Mac)
                # On Linux (Streamlit Cloud), you might need: "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
                title_font = ImageFont.truetype("arial.ttf", 60)
                subtitle_font = ImageFont.truetype("arial.ttf", 30)
                stat_font = ImageFont.truetype("arial.ttf", 40)
            except:
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
                stat_font = ImageFont.load_default()

            # 4. Helper to Center Text
            def draw_centered_text(text, y_pos, font, fill="white"):
                bbox = draw.textbbox((0, 0), text, font=font)
                text_w = bbox[2] - bbox[0]
                x_pos = (width - text_w) / 2
                
                # Draw a slight shadow for readability
                shadow_color = "black"
                draw.text((x_pos + 2, y_pos + 2), text, font=font, fill=shadow_color)
                draw.text((x_pos, y_pos), text, font=font, fill=fill)

            # 5. DRAW THE DATA
            # Title
            draw_centered_text(data['vibe_title'], 100, title_font, fill="#FFD700") # Gold
            
            # Subtitle
            draw_centered_text(data['vibe_subtitle'], 170, subtitle_font, fill="white")

            # Divider line
            draw.line((width*0.2, 220, width*0.8, 220), fill="white", width=3)

            # Stats Block (Middle)
            draw_centered_text(f"Top Day: {data['peak_shopping_day']}", 350, stat_font)
            draw_centered_text(f"Category: {data['top_category']}", 420, stat_font)
            
            # Fun Fact (Bottom)
            draw_centered_text(data['fun_fact'], 850, subtitle_font)

            # 6. Convert to Base64
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"

        except Exception as e:
            logger.error(f"Text Overlay Failed: {e}")
            return image_url # Return original URL if overlay fails

    def process(self, params, image_service=None, data_engine=None):
        contact_id = params["user_id"]
        
        # 1. Fetch Data
        try:
            df = data_engine.get_transaction_history(contact_id).collect()
        except:
            return {"error": "DB Error"}

        # 2. Stats
        if df.height == 0:
            # Handle empty data gracefully
            raw_stats = {"total_spend": 0, "total_items": 0, "top_day": "Unknown"}
            summary = "No data. Create a 'Mystery' vibe."
        else:
            # (Calculation logic omitted for brevity, same as before)
            raw_stats = {"total_spend": 2792.47, "total_items": 36, "top_day": "Tuesday"} # Example
            summary = str(raw_stats)

        # 3. Generate Content
        try:
            ai_output = self.chain.invoke({"transaction_summary": summary})
        except:
            # Fallback
            ai_output = {
                "vibe_title": "The Ghost Shopper",
                "vibe_subtitle": "Shopping in the shadows",
                "top_category": "Mystery",
                "peak_shopping_day": "Tuesday",
                "fun_fact": "You exist in the data void.",
                "image_prompt": "Dark abstract nebula background, empty center"
            }

        # 4. Generate Background Image
        bg_url = "https://images.unsplash.com/photo-1557683316-973673baf926"
        if self.image_gen:
            try:
                bg_url = self.image_gen.run(ai_output["image_prompt"])
            except: pass

        # 5. OVERLAY TEXT (The Magic Step)
        final_image_data = self._overlay_text_on_image(bg_url, ai_output)
        
        ai_output["generated_image"] = final_image_data

        return {
            "user_id": contact_id,
            "raw_stats": raw_stats,
            "ai_content": ai_output
        }