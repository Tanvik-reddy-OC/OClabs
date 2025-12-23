import streamlit as st
import requests
import json
import os
from typing import Dict, Any, List

# FastAPI Base URL
FASTAPI_BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://localhost:8000")

# --- Page Configuration ---
st.set_page_config(
    page_title="Optic Pulse",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Styling (UNCHANGED) ---
st.markdown("""
    <style>
    .main { background-color: #1a1a1a; color: #e0e0e0; }
    .st-emotion-cache-z5fcl4 { background-color: #2a2a2a; }
    .st-emotion-cache-z5fcl4 .st-bm { color: #e0e0e0; }
    h1, h2, h3, h4, h5, h6 { color: #00bcd4; }
    .stButton>button {
        background-color: #00796b;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 10px 20px;
        font-size: 16px;
    }
    .stButton>button:hover { background-color: #004d40; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Optic Pulse - AI Retail Suite")
st.markdown("Unlock AI-powered insights for your retail operations.")

# --- Sidebar Navigation ---
st.sidebar.header("Navigation")
feature_selection = st.sidebar.radio(
    "Choose a Feature",
    ["Vibe Report", "Brand Voice Cloner", "Smart Receipts"]
)

# ==========================================================
# ✅ VIBE REPORT (ONLY SECTION MODIFIED)
# ==========================================================
if feature_selection == "Vibe Report":
    st.header("✨ Vibe Report: Discover Customer Personas")
    st.write("Generate a 'wrapped-style' loyalty report for your customers.")

    with st.form("vibe_report_form"):
        user_id = st.text_input(
            "Customer User ID",
            help="Enter contactId / user_id from CSV"
        )
        submit_vibe = st.form_submit_button("Generate Vibe Report")

    if submit_vibe:
        if not user_id.strip():
            st.warning("Please enter a Customer User ID.")
            st.stop()

        payload = {"user_id": user_id.strip()}

        with st.spinner("Generating Vibe Report..."):
            try:
                response = requests.post(
                    f"{FASTAPI_BASE_URL}/process",
                    json=payload,
                    timeout=60
                )

                # ---- Handle backend errors safely ----
                if response.status_code != 200:
                    st.error("Backend error")
                    st.write("Status code:", response.status_code)
                    try:
                        st.json(response.json())
                    except Exception:
                        st.text("Raw response:")
                        st.text(response.text)
                    st.stop()

                # ---- Safe JSON parsing ----
                try:
                    api_response = response.json()
                except Exception:
                    st.error("API did not return valid JSON")
                    st.text(response.text)
                    st.stop()

                vibe_data = api_response.get("result")
                if not vibe_data:
                    st.error("Missing 'result' in API response")
                    st.json(api_response)
                    st.stop()

                # ---- UI rendering (UNCHANGED) ----
                st.success("Vibe Report Generated!")
                st.balloons()

                col1, col2 = st.columns(2)

                with col1:
                    st.subheader(f"Persona for @{vibe_data.get('user_id', 'N/A')}")
                    st.markdown(f"### {vibe_data.get('shopping_persona', 'N/A')}")

                    st.subheader("Behavioral Metrics")
                    for k, v in vibe_data.get("behavioral_metrics", {}).items():
                        st.write(f"**{k.replace('_',' ').title()}:** {v}")

                    st.subheader("Purchase Metrics")
                    for k, v in vibe_data.get("purchase_metrics", {}).items():
                        st.write(f"**{k.replace('_',' ').title()}:** {v}")

                    st.subheader("Color Palette Hints")
                    colors = vibe_data.get("color_palette_hints", [])
                    if colors:
                        for c in colors:
                            st.markdown(
                                f"<span style='background-color:{c}; padding:6px; border-radius:4px; margin-right:6px;'>{c}</span>",
                                unsafe_allow_html=True
                            )
                    else:
                        st.write("No color hints found.")

                with col2:
                    vibe_card_path = vibe_data.get("vibe_card_path")
                    if vibe_card_path:
                        filename = os.path.basename(vibe_card_path)
                        image_url = f"{FASTAPI_BASE_URL}/static/{filename}"

                        st.image(
                            image_url,
                            caption="Your Personalized Vibe Card",
                            use_column_width=True
                        )

                        st.download_button(
                            label="Download Vibe Card",
                            data=requests.get(image_url).content,
                            file_name=filename,
                            mime="image/png"
                        )
                    else:
                        st.warning("No vibe card image generated.")

            except requests.exceptions.RequestException as e:
                st.error("Could not connect to backend")
                st.text(str(e))

# ==========================================================
# ❌ BRAND VOICE CLONER (UNCHANGED)
# ==========================================================
elif feature_selection == "Brand Voice Cloner":
    st.header("✍️ Brand Voice Cloner")
    st.write("Analyze past campaign texts to generate new content.")

    with st.form("brand_voice_form"):
        campaign_texts_input = st.text_area(
            "Past Campaign Texts (one per line)",
            height=200
        )
        submit_brand_voice = st.form_submit_button("Generate New Campaign")

        if submit_brand_voice:
            campaign_texts = [
                t.strip() for t in campaign_texts_input.split("\n") if t.strip()
            ]
            response = requests.post(
                f"{FASTAPI_BASE_URL}/brand-voice",
                json={"campaign_texts": campaign_texts}
            )
            st.json(response.json())

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
                f"{FASTAPI_BASE_URL}/smart-receipt",
                json={
                    "user_id": customer_id,
                    "current_basket_items": current_basket_payload
                }
            )
            st.json(response.json())
