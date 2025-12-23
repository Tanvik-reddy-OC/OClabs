import streamlit as st
import requests
import json
import os
from typing import Dict, Any, List
from services.data_engine import DataEngine
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

/* App background */
.main {
    background-color: #121212;
    color: #eaeaea;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #1f1f1f;
}

/* Headings */
h1, h2, h3 {
    color: #00e5ff;
    letter-spacing: 0.5px;
}

/* Card container */
.card {
    background: linear-gradient(145deg, #1e1e1e, #262626);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.35);
    margin-bottom: 20px;
}

/* Buttons */
.stButton>button {
    background: linear-gradient(135deg, #00bfa5, #00796b);
    color: white;
    border-radius: 8px;
    border: none;
    padding: 10px 24px;
    font-size: 15px;
    font-weight: 600;
}

.stButton>button:hover {
    background: linear-gradient(135deg, #00e5ff, #00838f);
}

/* Text areas */
textarea {
    background-color: #1c1c1c !important;
    border-radius: 8px !important;
    border: 1px solid #333 !important;
}

/* Select / multiselect */
div[data-baseweb="select"] {
    background-color: #1c1c1c !important;
    border-radius: 8px;
}

/* Status boxes */
.stAlert {
    border-radius: 10px;
}

/* Success highlight */
.success-box {
    border-left: 5px solid #00e676;
    padding-left: 15px;
}

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
                f"{FASTAPI_BASE_URL}/smart-receipt",
                json={
                    "user_id": customer_id,
                    "current_basket_items": current_basket_payload
                }
            )
            st.json(response.json())
