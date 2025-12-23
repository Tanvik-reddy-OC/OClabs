import os
from PIL import Image, ImageDraw, ImageFont
import datetime

# Define directories (relative to the project root, assuming this script is in services/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Ensure static directory exists
os.makedirs(STATIC_DIR, exist_ok=True)

class ImageService:
    def __init__(self):
        # Create a placeholder template if it doesn't exist
        self._create_placeholder_template()

    def _create_placeholder_template(self, template_name="vibe_card_template.png"):
        template_path = os.path.join(ASSETS_DIR, template_name)
        if not os.path.exists(template_path):
            print(f"Placeholder template '{template_name}' not found. Creating a simple one.")
            # Ensure the assets directory exists before saving the file
            os.makedirs(ASSETS_DIR, exist_ok=True)
            # Create a simple white image
            img = Image.new('RGB', (800, 500), color = (255, 255, 255))
            d = ImageDraw.Draw(img)
            
            try:
                # Try to load a default font, fall back to generic if not found
                font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" # Common path on Linux
                if os.path.exists(font_path):
                    fnt = ImageFont.truetype(font_path, 40)
                else:
                    fnt = ImageFont.load_default()
                    print("Could not find a specific font, using default font for placeholder.")
            except Exception as e:
                fnt = ImageFont.load_default()
                print(f"Error loading font for placeholder: {e}, using default font.")

            d.text((50,50), "VIBE CARD TEMPLATE", fill=(0,0,0), font=fnt)
            d.text((50,150), "Customize this image in assets/vibe_card_template.png", fill=(0,0,0), font=ImageFont.load_default())
            img.save(template_path)
            print(f"Placeholder template saved to {template_path}")

    def generate_vibe_card(
        self,
        username: str,
        vibe_label: str,
        stats: dict
    ) -> str:
        """
        Generates a shareable vibe card image by overlaying text on a base template.
        Returns the file path of the generated image.
        """
        template_path = os.path.join(ASSETS_DIR, "vibe_card_template.png")
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Vibe card template not found at {template_path}")

        base_img = Image.open(template_path).convert("RGBA")
        draw = ImageDraw.Draw(base_img)

        # Try to load a font, fall back to default
        try:
            font_path_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            font_path_regular = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            
            if os.path.exists(font_path_bold):
                font_bold = ImageFont.truetype(font_path_bold, 36)
            else:
                font_bold = ImageFont.load_default()
                print("Could not find a specific bold font, using default.")
            
            if os.path.exists(font_path_regular):
                font_regular = ImageFont.truetype(font_path_regular, 24)
            else:
                font_regular = ImageFont.load_default()
                print("Could not find a specific regular font, using default.")

        except Exception as e:
            font_bold = ImageFont.load_default()
            font_regular = ImageFont.load_default()
            print(f"Error loading fonts: {e}, using default fonts.")

        text_color = (0, 0, 0, 255) # Black text

        # Add username and vibe label
        draw.text((50, 50), f"@{username}'s Optic Pulse", fill=text_color, font=font_bold)
        draw.text((50, 100), f"Vibe: {vibe_label}", fill=text_color, font=font_regular)

        # Add stats
        y_offset = 180
        for key, value in stats.items():
            stat_text = f"{key.replace('_', ' ').title()}: {value}"
            draw.text((50, y_offset), stat_text, fill=text_color, font=font_regular)
            y_offset += 30

        # Save the generated image
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        output_filename = f"vibe_card_{username}_{timestamp}.png"
        output_path = os.path.join(STATIC_DIR, output_filename)
        base_img.save(output_path)

        return output_path

# Example usage (for testing, not for production direct execution)
if __name__ == "__main__":
    image_service = ImageService()
    
    sample_username = "coolshopper"
    sample_vibe = "Eco-Conscious Explorer"
    sample_stats = {
        "total_spend_usd": 1250.75,
        "favorite_category": "Sustainable Apparel",
        "loyalty_points": 5000,
        "last_purchase_days_ago": 15
    }

    try:
        print("\nGenerating sample vibe card...")
        vibe_card_filepath = image_service.generate_vibe_card(
            username=sample_username,
            vibe_label=sample_vibe,
            stats=sample_stats
        )
        print(f"Vibe card generated at: {vibe_card_filepath}")
        # You can open this file to verify: os.system(f"xdg-open {vibe_card_filepath}")
    except Exception as e:
        print(f"Error generating vibe card: {e}")
