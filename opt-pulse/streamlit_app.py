import streamlit as st
import requests
import json
import os
from typing import Dict, Any, List

# FastAPI Base URL (assuming it's running locally on port 8000)
FASTAPI_BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://localhost:8000")

# --- Page Configuration ---
st.set_page_config(
    page_title="Optic Pulse",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS for dark mode feel and consumer product aesthetic
st.markdown("""
    <style>
    .main {
        background-color: #1a1a1a; /* Dark background */
        color: #e0e0e0; /* Light text */
    }
    .st-emotion-cache-z5fcl4 { /* Sidebar background */
        background-color: #2a2a2a;
    }
    .st-emotion-cache-z5fcl4 .st-bm { /* Sidebar text */
        color: #e0e0e0;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #00bcd4; /* Accent color for headers (e.g., Material Design Cyan) */
    }
    .stButton>button {
        background-color: #00796b; /* Dark Teal button */
        color: white;
        border-radius: 5px;
        border: none;
        padding: 10px 20px;
        font-size: 16px;
    }
    .stButton>button:hover {
        background-color: #004d40; /* Darker Teal on hover */
        color: white;
    }
    /* Input fields */
    .st-emotion-cache-1c7y2kl input, .st-emotion-cache-1c7y2kl textarea {
        background-color: #333333; /* Darker input fields */
        color: #e0e0e0;
        border: 1px solid #555555;
    }
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
      font-size: 1.1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #2a2a2a;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #00bcd4;
        color: white;
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

# --- Feature Content ---
if feature_selection == "Vibe Report":
    st.header("✨ Vibe Report: Discover Customer Personas")
    st.write("Generate a 'wrapped-style' loyalty report for your customers.")

    with st.form("vibe_report_form"):
        user_id = st.text_input("Customer User ID", help="Enter the unique ID of the customer.")
        submit_vibe = st.form_submit_button("Generate Vibe Report")

        if submit_vibe:
            if user_id:
                try:
                    with st.spinner("Generating Vibe Report..."):
                        response = requests.post(f"{FASTAPI_BASE_URL}/vibe-report", json={"user_id": user_id})
                        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                        vibe_data = response.json()
                    
                    st.success("Vibe Report Generated!")
                    st.balloons()

                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader(f"Persona for @{vibe_data.get('user_id', 'N/A')}")
                        st.markdown(f"### {vibe_data.get('shopping_persona', 'No persona found')}")
                        
                        st.subheader("Behavioral Metrics")
                        for k, v in vibe_data.get('behavioral_metrics', {}).items():
                            st.write(f"**{k.replace('_', ' ').title()}:** {v}")
                        
                        st.subheader("Purchase Metrics")
                        for k, v in vibe_data.get('purchase_metrics', {}).items():
                            st.write(f"**{k.replace('_', ' ').title()}:** {v}")
                        
                        st.subheader("Color Palette Hints")
                        colors = vibe_data.get('color_palette_hints', [])
                        if colors:
                            st.write(", ".join(colors))
                            for color_hex in colors:
                                st.markdown(f"<span style='background-color:{color_hex}; padding: 5px; border-radius: 3px;'>{color_hex}</span>", unsafe_allow_html=True)
                        else:
                            st.write("No color hints found.")

                    with col2:
                        vibe_card_path = vibe_data.get('vibe_card_path')
                        if vibe_card_path:
                            # FastAPI serves static files at /static/{filename}
                            card_filename = os.path.basename(vibe_card_path)
                            st.image(f"{FASTAPI_BASE_URL}/static/{card_filename}", caption="Your Personalized Vibe Card", use_column_width=True)
                            st.download_button(
                                label="Download Vibe Card",
                                data=requests.get(f"{FASTAPI_BASE_URL}/static/{card_filename}").content,
                                file_name=card_filename,
                                mime="image/png"
                            )
                        else:
                            st.warning("No vibe card image generated.")

                except requests.exceptions.RequestException as e:
                    st.error(f"API Error: {e}")
                    if response is not None:
                        st.json(response.json()) # Display API error details if available
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")
            else:
                st.warning("Please enter a Customer User ID.")

elif feature_selection == "Brand Voice Cloner":
    st.header("✍️ Brand Voice Cloner: Craft Compelling Campaigns")
    st.write("Analyze past campaign texts to generate new content in your brand's voice with a predicted success score.")

    with st.form("brand_voice_form"):
        campaign_texts_input = st.text_area(
            "Past Campaign Texts (one per line)",
            "Enter at least 3-5 examples of your past campaign messages. Each new line will be considered a separate campaign text.",
            height=200
        )
        submit_brand_voice = st.form_submit_button("Generate New Campaign")

        if submit_brand_voice:
            campaign_texts = [text.strip() for text in campaign_texts_input.split('\n') if text.strip()]
            if campaign_texts:
                try:
                    with st.spinner("Cloning brand voice and generating campaign..."):
                        response = requests.post(f"{FASTAPI_BASE_URL}/brand-voice", json={"campaign_texts": campaign_texts})
                        response.raise_for_status()
                        brand_voice_data = response.json()
                    
                    st.success("New Campaign Generated!")
                    st.subheader("Generated Campaign Body:")
                    st.markdown(f"```\n{brand_voice_data.get('new_campaign_body', 'N/A')}\n```")
                    st.subheader("Predicted Success Score:")
                    score = brand_voice_data.get('predicted_success_score', 0)
                    st.metric(label="Success Score (0-100)", value=f"{score}%")

                except requests.exceptions.RequestException as e:
                    st.error(f"API Error: {e}")
                    if response is not None:
                        st.json(response.json())
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")
            else:
                st.warning("Please enter some past campaign texts.")

elif feature_selection == "Smart Receipts":
    st.header("🛍️ Smart Receipts: Hyper-Personalized Recommendations")
    st.write("Offer intelligent product recommendations, loyalty incentives, and coupons on digital receipts.")

    with st.form("smart_receipt_form"):
        customer_id = st.text_input("Customer User ID", help="Enter the unique ID of the customer.")
        st.subheader("Current Basket Items")
        # Dynamic input for current basket items
        if 'basket_items' not in st.session_state:
            st.session_state.basket_items = []

        def add_item():
            st.session_state.basket_items.append({"item_name": "", "price": 0.0, "quantity": 1})

        def remove_item(index):
            if index < len(st.session_state.basket_items):
                st.session_state.basket_items.pop(index)

        add_item_button = st.form_submit_button("Add Item to Basket")
        if add_item_button:
            add_item() # Add item when button is clicked

        current_basket_payload: List[Dict[str, Any]] = []
        for i, item in enumerate(st.session_state.basket_items):
            cols = st.columns([0.4, 0.2, 0.2, 0.2])
            with cols[0]:
                item_name = st.text_input(f"Item Name {i+1}", value=item.get("item_name", ""), key=f"item_name_{i}")
            with cols[1]:
                price = st.number_input(f"Price {i+1}", value=float(item.get("price", 0.0)), min_value=0.0, format="%.2f", key=f"price_{i}")
            with cols[2]:
                quantity = st.number_input(f"Quantity {i+1}", value=int(item.get("quantity", 1)), min_value=1, step=1, key=f"quantity_{i}")
            with cols[3]:
                st.markdown("<br>", unsafe_allow_html=True) # Spacer for alignment
                remove_btn = st.form_submit_button("Remove", key=f"remove_item_{i}")
                if remove_btn:
                    remove_item(i)
                    st.experimental_rerun() # Rerun to update the list

            if item_name and price > 0 and quantity > 0:
                current_basket_payload.append({
                    "item_id": f"item_{i}", # Dummy ID for now
                    "item_name": item_name,
                    "price": price,
                    "quantity": quantity
                })
        
        # Ensure 'Add Item' button works initially
        if not st.session_state.basket_items:
            if st.form_submit_button("Add First Item"):
                add_item()
                st.experimental_rerun()


        submit_smart_receipt = st.form_submit_button("Get Smart Recommendations")

        if submit_smart_receipt:
            if customer_id and current_basket_payload:
                try:
                    with st.spinner("Generating smart receipt recommendations..."):
                        payload = {
                            "user_id": customer_id,
                            "current_basket_items": current_basket_payload
                        }
                        response = requests.post(f"{FASTAPI_BASE_URL}/smart-receipt", json=payload)
                        response.raise_for_status()
                        smart_receipt_data = response.json()
                    
                    st.success("Smart Receipt Recommendations Generated!")
                    st.subheader("Next Best Item:")
                    next_item = smart_receipt_data.get('next_best_item')
                    if next_item:
                        st.write(f"**{next_item.get('item_name', 'N/A')}** (ID: {next_item.get('item_id', 'N/A')})")
                    else:
                        st.write("No specific item recommendation at this time.")
                    
                    st.subheader("Loyalty Incentive:")
                    st.info(smart_receipt_data.get('loyalty_incentive_text', 'N/A'))
                    
                    st.subheader("Coupons:")
                    coupons = smart_receipt_data.get('coupons', [])
                    if coupons:
                        for coupon in coupons:
                            st.code(coupon)
                    else:
                        st.write("No coupons available.")

                except requests.exceptions.RequestException as e:
                    st.error(f"API Error: {e}")
                    if response is not None:
                        st.json(response.json())
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")
            else:
                st.warning("Please enter a Customer User ID and add at least one item to the basket.")
