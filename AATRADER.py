import streamlit as st
import re
import json
import pandas as pd
from datetime import date
from thefuzz import process

# --- PAGE CONFIG ---
st.set_page_config(page_title="Cyber Trader Suite", page_icon="⚖️", layout="wide")

# --- ALIAS LIST ---
# Force "lar" to become "LAR", etc.
ALIASES = {
    "lar": "LAR",       
    "m16": "M16",       
    "m4": "M4-A1",      
    "ak": "KA-74",      
    "vs": "VSS"
}

# --- CUSTOM CSS (THEME ENGINE) ---
def set_theme():
    st.markdown("""
    <style>
        /* 1. Main Background & Global Text */
        .stApp {
            background-color: #0E1117;
            color: #E0E0E0; /* Light Gray for general text */
        }
        
        /* 2. Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #262730;
        }
        section[data-testid="stSidebar"] * {
            color: #FAFAFA !important; /* Bright white for sidebar */
        }
        
        /* 3. Input Labels (The text above boxes) */
        .stTextArea label, .stTextInput label, .stNumberInput label, .stDateInput label, .stCheckbox label {
            color: #B0B0B0 !important; /* Light Gray for readability */
            font-size: 1rem;
            font-weight: bold;
        }
        
        /* 4. Input Boxes (The inside part) */
        .stTextArea textarea, .stTextInput input {
            background-color: #1E1E1E !important; 
            color: #00FF00 !important; /* Matrix Green Text */
            border: 1px solid #4CAF50; 
            caret-color: #00FF00;
        }
        
        /* 5. Buttons */
        .stButton>button {
            color: #FAFAFA; 
            background-color: #262730; 
            border: 1px solid #4CAF50;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #4CAF50; 
            color: #000000; 
            box-shadow: 0 0 10px #4CAF50;
        }
        
        /* 6. TABLE STYLING (The fix for the white box) */
        table {
            color: #E0E0E0 !important; /* Light Gray Text */
            background-color: transparent !important; /* Remove white background */
            border-collapse: collapse;
            width: 100%;
        }
        thead tr th {
            background-color: #262730 !important;
            color: #00FF00 !important; /* Green Headers */
            border-bottom: 2px solid #4CAF50 !important;
        }
        tbody tr {
            border-bottom: 1px solid #333 !important;
        }
        tbody tr:hover {
            background-color: #1E1E1E !important; /* Slight highlight on hover */
        }
        td {
            color: #E0E0E0 !important; /* Light Gray Cells */
        }
        
        /* 7. Success/Metric Text */
        [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
            color: #4CAF50 !important;
        }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIC FUNCTIONS ---
def load_prices():
    try:
        with open('prices.json', 'r') as f:
            return json.load(f)
    except Exception:
        return {"WE_BUY": {}, "WE_SELL": {}}

def clean_text(text):
    # Removes hidden formatting characters
    return re.sub(r'[^a-zA-Z0-9\- ]', '', text)

def smart_parse_line(line, price_dict):
    # 1. Sanitize
    line = clean_text(line).lower().strip()
    if not line or len(line) < 2: return None

    # 2. Extract Quantity
    quantity = 1
    match_start = re.match(r'^(\d+)\s+', line)
    match_end = re.search(r'\s+(\d+)$', line)

    item_clean = line
    if match_start:
        quantity = int(match_start.group(1))
        item_clean = line[match_start.end():].strip()
    elif match_end:
        quantity = int(match_end.group(1))
        item_clean = line[:match_end.start()].strip()
    
    # 3. Apply Alias
    if item_clean in ALIASES:
        item_clean = ALIASES[item_clean]
        is_aliased = True
    else:
        is_aliased = False

    # 4. Special Item Check
    if 'special_name' in globals() and special_name and special_name.lower() in item_clean.lower():
         return {"Item": f"🔥 {special_name}", "Qty": quantity, "Unit Price": special_price, "Total": quantity * special_price}

    # 5. EXACT MATCH
    exact_map = {k.lower(): k for k in price_dict}
    search_term = item_clean.lower()
    
    if search_term in exact_map:
        real_key = exact_map[search_term]
        return {"Item": real_key, "Qty": quantity, "Unit Price": price_dict[real_key], "Total": quantity * price_dict[real_key]}

    # 6. STOP IF ALIASED (Missing Item Trap)
    if is_aliased:
        return {"Item": f"❌ MISSING: {item_clean}", "Qty": quantity, "Unit Price": 0, "Total": 0}

    # 7. FUZZY MATCH
    choices = list(price_dict.keys())
    match, score = process.extractOne(item_clean, choices)
    
    # Strict Guard for short words
    if len(item_clean) <= 4:
        if item_clean.lower() not in match.lower():
            return None 

    if score >= 80:
        return {"Item": match, "Qty": quantity, "Unit Price": price_dict[match], "Total": quantity * price_dict[match]}
    
    return None

def render_tab(df_key, price_dict, type_label):
    st.subheader(f"📊 {type_label} Calculation")
    input_text = st.text_area(f"Paste {type_label} list here:", height=150, key=f"text_{df_key}")
    
    if st.button(f"🚀 Process {type_label}", key=f"btn_{df_key}"):
        lines = input_text.split('\n')
        results = []
        for line in lines:
            parsed = smart_parse_line(line, price_dict)
            if parsed: results.append(parsed)
        
        if results: st.session_state[df_key] = pd.DataFrame(results)
        else: st.warning("No matches found.")

    df = st.session_state[df_key]
    if not df.empty and "Item" in df.columns:
        # Create a copy for formatting (Add commas)
        formatted_df = df.copy()
        formatted_df["Unit Price"] = formatted_df["Unit Price"].apply(lambda x: f"{x:,}")
        formatted_df["Total"] = formatted_df["Total"].apply(lambda x: f"{x:,}")
        
        # USE st.table INSTEAD OF st.dataframe TO FORCE DARK THEME
        st.table(formatted_df[["Item", "Qty", "Unit Price", "Total"]])
        
        total_sum = df["Total"].sum()
        st.success(f"### Total {type_label} Value: {total_sum:,}")

def clear_state():
    st.session_state.buy_df = pd.DataFrame()
    st.session_state.sell_df = pd.DataFrame()
    st.session_state["text_buy_df"] = ""
    st.session_state["text_sell_df"] = ""

def main():
    set_theme()
    st.title("⚖️ Cyber Trader Economy Suite")
    
    # Sidebar
    st.sidebar.header("🔥 Item of the Week")
    global special_name, special_price
    special_item_active = st.sidebar.checkbox("Enable Special Price")
    special_name = st.sidebar.text_input("Item Name (e.g. Gas Stove)")
    special_price_val = st.sidebar.text_input("Special Price", value="0")
    try: special_price = int(special_price_val)
    except: special_price = 0
    expiry_date = st.sidebar.date_input("Offer Ends On", min_value=date.today())
    if st.sidebar.button("🔄 Update Promo"): st.rerun()

    data = load_prices()
    WE_BUY = data.get("WE_BUY", {})
    WE_SELL = data.get("WE_SELL", {})

    if 'buy_df' not in st.session_state: st.session_state.buy_df = pd.DataFrame()
    if 'sell_df' not in st.session_state: st.session_state.sell_df = pd.DataFrame()

    tab1, tab2 = st.tabs(["💰 WE BUY (Payout)", "🛒 WE SELL (Cost)"])
    with tab1: render_tab("buy_df", WE_BUY, "Payout")
    with tab2: render_tab("sell_df", WE_SELL, "Cost")
    st.button("🗑️ Clear All", on_click=clear_state)

if __name__ == "__main__":
    main()
