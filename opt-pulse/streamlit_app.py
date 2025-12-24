import streamlit as st
import requests
import os
from typing import Dict, Any, List
from services.data_engine import DataEngine

FASTAPI_BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://localhost:8000")

# --------------------------------------------------
# Page Config
# --------------------------------------------------
st.set_page_config(
    page_title="Optic Pulse",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# Global Styling
# --------------------------------------------------
st.markdown("""
<style>
.main {
    background-color: #121212;
    color: #eaeaea;
}

section[data-testid="stSidebar"] {
    background-color: #1f1f1f;
}

h1, h2, h3 {
    color: #00e5ff;
}

.card {
    background: linear-gradient(145deg, #1e1e1e, #262626);
    border-radius: 14px;
    padding: 20px;
    box-shadow: 0 10px 28px rgba(0,0,0,0.4);
}

.stButton>button {
    background: linear-gradient(135deg, #00bfa5, #00796b);
    color: white;
    border-radius: 10px;
    border: none;
    padding: 12px 26px;
    font-size: 16px;
    font-weight: 600;
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Space+Grotesk:wght@500;700&display=swap');

/* The Phone Container */
.phone-container {
    background: #000;
    border-radius: 40px;
    padding: 15px;
    max-width: 400px;
    margin: 0 auto;
    box-shadow: 0 20px 50px rgba(0,0,0,0.5);
    border: 8px solid #333;
    position: relative;
    overflow: hidden;
}

/* The Vibe Card Gradient Background */
.vibe-gradient-bg {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: 30px;
    padding: 30px 20px;
    color: white;
    font-family: 'Inter', sans-serif;
    min-height: 600px;
    position: relative;
}

/* Header Section */
.vibe-header {
    text-align: center;
    margin-bottom: 30px;
}
.vibe-year {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 14px;
    letter-spacing: 2px;
    text-transform: uppercase;
    opacity: 0.8;
}
.vibe-main-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 32px;
    font-weight: 800;
    background: linear-gradient(to right, #fff, #a5b4fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-top: 10px;
    line-height: 1.1;
}

/* The "Bento Box" Grid Stats */
.stats-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 15px;
    margin-top: 20px;
}

.stat-box {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 20px;
    padding: 20px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    transition: transform 0.2s;
}

.stat-box:hover {
    transform: translateY(-5px);
    background: rgba(255, 255, 255, 0.15);
}

.stat-label {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
    opacity: 0.7;
    margin-bottom: 5px;
}

.stat-value {
    font-size: 24px;
    font-weight: 700;
}

/* Highlight Box (Like the Weekend Warrior) */
.highlight-box {
    background: linear-gradient(135deg, #6366f1, #a855f7);
    border-radius: 24px;
    padding: 25px;
    text-align: center;
    margin-bottom: 20px;
    box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4);
}

.highlight-title {
    font-size: 26px;
    font-weight: 800;
    font-family: 'Space Grotesk', sans-serif;
    margin-bottom: 5px;
}

.highlight-sub {
    font-size: 14px;
    opacity: 0.9;
}

/* Color Vibe Strip */
.color-vibe-strip {
    display: flex;
    align-items: center;
    background: rgba(0,0,0,0.3);
    border-radius: 16px;
    padding: 10px 15px;
    margin-top: 15px;
}
.color-swatch {
    width: 40px;
    height: 40px;
    border-radius: 12px;
    margin-right: 15px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

/* Footer Share Button Look */
.share-btn {
    background: white;
    color: black;
    text-align: center;
    padding: 15px;
    border-radius: 50px;
    font-weight: 700;
    margin-top: 30px;
    cursor: pointer;
    box-shadow: 0 10px 20px rgba(0,0,0,0.2);
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# App Header
# --------------------------------------------------
st.title("⚡ Optic Pulse")
st.caption("AI-powered retail intelligence")

# --------------------------------------------------
# Sidebar
# --------------------------------------------------
st.sidebar.header("Navigation")
feature_selection = st.sidebar.radio(
    "Choose a Feature",
    ["Vibe Report", "Brand Voice Cloner", "Smart Receipts"]
)

if feature_selection == "Vibe Report":
    st.header("✨ Vibe Report")
    
    with st.form("vibe_report_form"):
        user_id = st.text_input("Customer User ID", value="20186130") # Default for testing
        submit_vibe = st.form_submit_button("Generate Vibe Report")

    if submit_vibe:
        with st.spinner("Analyzing purchase history & calculating vibe..."):
            try:
                response = requests.post(
                    f"{FASTAPI_BASE_URL}/process",
                    json={"user_id": user_id.strip(), "agent_type": "vibe_report"},
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    result = data.get("result", {})
                    
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        ai_content = result.get("ai_content", {})
                        raw_stats = result.get("raw_stats", {})

                        # -------------------------
                        # RENDER THE UI CARD
                        # -------------------------
                        col1, col2, col3 = st.columns([1, 1.5, 1])
                        
                        with col2:
                            # Dynamic HTML Injection
                            st.markdown(f"""
                            <div class="phone-container">
                                <div class="vibe-gradient-bg">
                                    <div class="vibe-header">
                                        <div class="vibe-year">YOUR 2024</div>
                                        <div class="vibe-main-title">Retail Wrapped</div>
                                    </div>

                                    <div class="highlight-box">
                                        <div class="highlight-title">{ai_content.get('vibe_title', 'The Shopper')}</div>
                                        <div class="highlight-sub">{ai_content.get('vibe_subtitle', 'Always on trend.')}</div>
                                    </div>

                                    <div class="stats-grid">
                                        <div class="stat-box">
                                            <div class="stat-label">🛍️ Top Category</div>
                                            <div class="stat-value">{ai_content.get('top_category', 'General')}</div>
                                        </div>
                                        
                                        <div class="stat-box">
                                            <div class="stat-label">📅 Peak Day</div>
                                            <div class="stat-value">{raw_stats.get('top_day', 'Saturday')}</div>
                                        </div>

                                        <div class="stat-box">
                                            <div class="stat-label">🏆 Fun Fact</div>
                                            <div style="font-size: 14px; line-height: 1.4;">
                                                {ai_content.get('fun_fact', 'You are a star shopper!')}
                                            </div>
                                        </div>
                                    </div>

                                    <div class="color-vibe-strip">
                                        <div class="color-swatch" style="background-color: {ai_content.get('color_vibe', '#7c3aed')}"></div>
                                        <div>
                                            <div style="font-size: 10px; opacity: 0.7;">YOUR COLOR AURA</div>
                                            <div style="font-weight: 600;">{ai_content.get('color_name', 'Royal Purple')}</div>
                                        </div>
                                    </div>
                                    
                                    <div class="share-btn">
                                        Total Spend: ₹{raw_stats.get('total_spend', 0)}
                                    </div>

                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                else:
                    st.error(f"Error: {response.text}")
            except Exception as e:
                st.error(f"Connection Error: {e}")
    st.markdown(custom_css + html_content, unsafe_allow_html=True)

# ==========================================================
# ❌ BRAND VOICE CLONER (UNCHANGED)
# ==========================================================
if feature_selection == "Brand Voice Cloner":
    st.header("✍️ Brand Voice Cloner")
    st.caption("Learn from past campaigns and generate high-impact messaging")

    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)

        @st.cache_data(show_spinner=False)
        def load_contact_ids():
            engine = DataEngine()
            df = engine.get_contact_ids().collect()
            return df["cid"].to_list()

        contact_ids = load_contact_ids()

        selected_cids = st.multiselect(
            "👥 Select Target Contacts",
            contact_ids,
            help="These users will be analyzed as a group persona"
        )

        generate = st.button("🚀 Generate Campaign")

        st.markdown('</div>', unsafe_allow_html=True)

    if generate:
        if not selected_cids:
            st.error("Select at least one contact")
        else:
            with st.spinner("Analyzing brand voice & user behavior..."):
                response = requests.post(
                    f"{FASTAPI_BASE_URL}/process",
                    json={
                        "agent_type": "brand_voice",
                        "contact_ids": selected_cids
                    }
                )

            if response.status_code == 200:
                data = response.json()
                if data.get("success", False):
                    result = data.get("result", {})

                    st.markdown('<div class="card success-box">', unsafe_allow_html=True)
                    st.subheader("✨ Generated Campaign")

                    st.text_area(
                        "Campaign Body",
                        value=result.get("new_campaign_body", ""),
                        height=220
                    )

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(
                            "Predicted Success",
                            f"{result.get('predicted_success_score', 0)} / 100"
                        )

                    with col2:
                        st.write("**Learned Patterns**")
                        st.json(result.get("inferred_patterns", {}))

                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.error("Failed to generate campaign. Please try again.")
            else:
                st.error(f"Error from server: {response.text}")

# ==========================================================
# ❌ SMART RECEIPTS (UNCHANGED)
# ==========================================================
elif feature_selection == "Smart Receipts":
    st.header("🛍️ Smart Receipts")
    st.write("Hyper-personalized receipt recommendations.")

    with st.form("smart_receipt_form"):
        customer_id = st.text_input("Customer User ID")

        if "basket_items" not in st.session_state:
            st.session_state.basket_items = []

        def add_item():
            st.session_state.basket_items.append(
                {"item_name": "", "price": 0.0, "quantity": 1}
            )

        if st.form_submit_button("Add Item"):
            add_item()

        current_basket_payload: List[Dict[str, Any]] = []

        for i, item in enumerate(st.session_state.basket_items):
            cols = st.columns(3)
            with cols[0]:
                item_name = st.text_input(
                    f"Item Name {i+1}",
                    key=f"item_name_{i}"
                )
            with cols[1]:
                price = st.number_input(
                    f"Price {i+1}",
                    min_value=0.0,
                    key=f"price_{i}"
                )
            with cols[2]:
                quantity = st.number_input(
                    f"Qty {i+1}",
                    min_value=1,
                    step=1,
                    key=f"qty_{i}"
                )

            if item_name and price > 0:
                current_basket_payload.append({
                    "item_id": f"item_{i}",
                    "item_name": item_name,
                    "price": price,
                    "quantity": quantity
                })

        submit_receipt = st.form_submit_button("Get Smart Recommendations")

        if submit_receipt:
            response = requests.post(
                f"{FASTAPI_BASE_URL}/process",
                json={
                    "query" : "Generate smart receipt recommendations for the current purchase.You are only allowed to recommend items from the provided inventory SKU list.Do NOT invent or suggest any product that is not present in the inventory Decision priority: 1. Select complementary items from the inventory that are closely related to the current basket items (same category, usage, or frequently co-purchased). 2. If no strong complement exists, select items from the inventory that match the customer’s past purchase patterns. 3. If neither applies, provide a non-product contextual tip (for example: usage advice or seasonal suggestion) instead of recommending a product. Rules: All recommended products must exist in the provided SKU inventory.If no suitable SKU exists, return a helpful tip instead of a product.Recommend at most 3 items.Each recommendation must include a short reason. Output must be concise and suitable for a digital receipt.",
                    "user_id": customer_id,
                    "current_basket_items": current_basket_payload
                }
            )
            st.json(response.json())
