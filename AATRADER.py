import streamlit as st
import re
import json
import pandas as pd
from datetime import date
from thefuzz import process

# --- PAGE CONFIG ---
st.set_page_config(page_title="Cyber Trader Suite", page_icon="⚖️", layout="wide")

# --- CUSTOM CSS FOR CYBER/NIGHT MODE ---
def set_theme():
    st.markdown("""
    <style>
        /* Force Dark Background */
        .stApp {
            background-color: #0E1117;
            color: #FAFAFA;
        }
        
        /* Customize Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #262730;
        }
        
        /* Cyber Text Areas */
        .stTextArea textarea {
            background-color: #1E1E1E !important;
            color: #00FF00 !important; /* Green Text */
            border: 1px solid #4CAF50;
            font-family: 'Courier New', monospace; /* Terminal look */
        }
        
        /* Cyber Buttons */
        .stButton>button {
            color: #FAFAFA;
            background-color: #262730;
            border: 1px solid #4CAF50;
            transition: all 0.3s ease;
        }
        
        /* Button Hover Effect */
        .stButton>button:hover {
            background-color: #4CAF50;
            color: #000000;
            border-color: #00FF00;
            box-shadow: 0 0 10px #4CAF50; /* Neon Glow */
        }
        
        /* Tables */
        thead tr th:first-child {display:none}
        tbody th {display:none}
        
        /* Headers */
        h1, h2, h3 {
            color: #FAFAFA !important;
        }
        
        /* Success/Metric Text */
        [data-testid="stMetricValue"] {
            color: #4CAF50 !important;
        }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: ITEM OF THE WEEK ---
st.sidebar.header("🔥 Item of the Week")
st.sidebar.markdown("Set a temporary special price for a specific item.")

special_item_active = st.sidebar.checkbox("Enable Special Price")
special_name = st.sidebar.text_input("Item Name (e.g. Gas Stove)")
special_price = st.sidebar.number_input("Special Price", min_value=0, step=100)
expiry_date = st.sidebar.date_input("Offer Ends On", min_value=date.today())

# Check if offer is expired
is_expired = date.today() > expiry_date
if special_item_active and is_expired:
    st.sidebar.error(f"⚠️ Offer expired on {expiry_date}")

# --- LOGIC FUNCTIONS ---
def load_prices():
    try:
        with open('prices.json', 'r') as f:
            return json.load(f)
    except Exception:
        # Returns empty structure if file is missing or broken
        return {"WE_BUY": {}, "WE_SELL": {}}

def smart_parse_line(line, price_dict):
    """
    Parses a single line of text to extract quantity and item name.
    Prioritizes the 'Special Item' over fuzzy matching.
    """
    line = line.lower().strip()
    
    # 1. Basic garbage check
    if not line or len(line) < 2:
        return None

    # 2. EXTRACT QUANTITY (Find digits anywhere in the line)
    nums = re.findall(r'\d+', line)
    quantity = int(nums[0]) if nums else 1
    
    # 3. CLEAN ITEM NAME (Remove digits and dashes)
    item_clean = re.sub(r'\d+', '', line)
    item_clean = item_clean.replace('-', ' ').strip()
    
    # 4. PRIORITY CHECK: SPECIAL ITEM
    # Checks this FIRST so it registers even if inside an "Item of the week" line
    if special_item_active and not is_expired and special_name:
        if special_name.lower() in item_clean:
             return {
                "Item": f"🔥 {special_name} (SPECIAL)", 
                "Qty": quantity, 
                "Unit Price": special_price, 
                "Total": quantity * special_price
            }

    # 5. IGNORE RULE
    # If it wasn't the special item, AND it says "item of the week", ignore it.
    if "item of the week" in line:
        return None

    # 6. FUZZY MATCH (Standard Items)
    if not item_clean:
        return None

    choices = list(price_dict.keys())
    if not choices:
        return None
        
    match, score = process.extractOne(item_clean, choices)
    
    # Threshold set to 80 to avoid false positives
    if score >= 80:
        price = price_dict[match]
        return {
            "Item": match, 
            "Qty": quantity, 
            "Unit Price": price, 
            "Total": quantity * price
        }
    return None

def render_tab(df_key, price_dict, type_label):
    st.subheader(f"📊 {type_label} Calculation")
    
    input_text = st.text_area(f"Paste {type_label} list here:", height=150, key=f"text_{df_key}")
    
    if st.button(f"🚀 Process {type_label}", key=f"btn_{df_key}"):
        lines = input_text.split('\n')
        results = []
        for line in lines:
            parsed = smart_parse_line(line, price_dict)
            if parsed:
                results.append(parsed)
        
        if results:
            st.session_state[df_key] = pd.DataFrame(results)
        else:
            st.warning("No matches found.")

    # Display Table Logic
    df = st.session_state[df_key]
    if not df.empty and "Item" in df.columns:
        formatted_df = df.copy()
        formatted_df["Unit Price"] = formatted_df["Unit Price"].apply(lambda x: f"{x:,}")
        formatted_df["Total"] = formatted_df["Total"].apply(lambda x: f"{x:,}")
        
        st.table(formatted_df[["Item", "Qty", "Unit Price", "Total"]])
        
        # Calculate Sum from original numeric data
        total_sum = df["Total"].sum()
        st.success(f"### Total {type_label} Value: {total_sum:,}")

# --- MAIN APP ---
def main():
    set_theme() # <--- INJECT CUSTOM THEME
    st.title("⚖️ Cyber Trader Economy Suite")
    
    # Show active promo banner
    if special_item_active and not is_expired and special_name:
        st.info(f"🔥 **ACTIVE PROMO:** {special_name} @ {special_price:,} until {expiry_date}")

    data = load_prices()
    WE_BUY = data.get("WE_BUY", {})
    WE_SELL = data.get("WE_SELL", {})

    # Initialize session states
    if 'buy_df' not in st.session_state:
        st.session_state.buy_df = pd.DataFrame()
    if 'sell_df' not in st.session_state:
        st.session_state.sell_df = pd.DataFrame()

    tab1, tab2 = st.tabs(["💰 WE BUY (Payout)", "🛒 WE SELL (Cost)"])

    with tab1:
        render_tab("buy_df", WE_BUY, "Payout")

    with tab2:
        render_tab("sell_df", WE_SELL, "Cost")

    if st.button("🗑️ Clear All"):
        st.session_state.buy_df = pd.DataFrame()
        st.session_state.sell_df = pd.DataFrame()
        st.rerun()

if __name__ == "__main__":
    main()
