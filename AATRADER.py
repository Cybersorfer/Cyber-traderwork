import streamlit as st
import re
import json
import pandas as pd
from datetime import date
from thefuzz import process

# --- PAGE CONFIG ---
st.set_page_config(page_title="Cyber Trader Suite", page_icon="⚖️", layout="wide")

# --- ALIAS LIST ---
ALIASES = {
    "lar": "LAR",       
    "m16": "M16",       
    "m4": "M4-A1",      
    "ak": "KA-74",      
    "vs": "VSS"
}

# --- CUSTOM CSS ---
def set_theme():
    st.markdown("""
    <style>
        .stApp { background-color: #0E1117; color: #E0E0E0; }
        section[data-testid="stSidebar"] { background-color: #262730; }
        section[data-testid="stSidebar"] * { color: #FAFAFA !important; }
        .stTextArea label, .stTextInput label, .stNumberInput label, .stDateInput label, .stCheckbox label {
            color: #B0B0B0 !important; font-size: 1rem; font-weight: bold;
        }
        .stTextArea textarea, .stTextInput input {
            background-color: #1E1E1E !important; color: #00FF00 !important;
            border: 1px solid #4CAF50; caret-color: #00FF00;
        }
        .stButton>button {
            color: #FAFAFA; background-color: #262730; border: 1px solid #4CAF50; transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #4CAF50; color: #000000; box-shadow: 0 0 10px #4CAF50;
        }
        table { color: #E0E0E0 !important; background-color: transparent !important; border-collapse: collapse; width: 100%; }
        thead tr th { background-color: #262730 !important; color: #00FF00 !important; border-bottom: 2px solid #4CAF50 !important; }
        tbody tr { border-bottom: 1px solid #333 !important; }
        tbody tr:hover { background-color: #1E1E1E !important; }
        td { color: #E0E0E0 !important; }
        [data-testid="stMetricValue"], [data-testid="stMetricLabel"] { color: #4CAF50 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIC FUNCTIONS ---
def load_prices():
    try:
        with open('prices.json', 'r') as f:
            return json.load(f)
    except Exception:
        return {"WE_BUY": {}, "WE_SELL": {}}

def detect_intent_and_clean(line):
    """
    Determines if the line is for PAYOUT (User sells) or COST (User buys).
    Also strips the 'intent' keywords so we can find the quantity easier.
    """
    line_lower = line.lower()
    
    # default intent is whatever tab we are in, BUT:
    # If explicitly "buying/ordering", it goes to SELL_DF (Cost to player)
    # If explicitly "selling", it goes to BUY_DF (Payout to player)
    
    intent = "NEUTRAL" 
    
    # Keywords indicating Player wants to BUY (Cost)
    buy_keywords = ["want to buy", "buying", "wtb", "want to order", "ordering", "need"]
    for kw in buy_keywords:
        if kw in line_lower:
            intent = "PLAYER_BUYS" # Goes to WE_SELL tab
            # Strip the keyword to help quantity detection
            line = re.sub(kw, "", line, flags=re.IGNORECASE)
            break
            
    # Keywords indicating Player wants to SELL (Payout)
    sell_keywords = ["want to sell", "selling", "wts", "i have", "have"]
    if intent == "NEUTRAL":
        for kw in sell_keywords:
            if kw in line_lower:
                intent = "PLAYER_SELLS" # Goes to WE_BUY tab
                line = re.sub(kw, "", line, flags=re.IGNORECASE)
                break
                
    return intent, line

def clean_text(text):
    # Removes formatting but KEEPS 'x', '-', and '.'
    return re.sub(r'[^a-zA-Z0-9\-\. ]', '', text)

def smart_parse_line(line, price_dict):
    # 0. Pre-Clean: Remove "locker code" garbage to prevent false matches
    if "locker code" in line.lower() or "combo" in line.lower():
        return None

    # 1. Sanitize
    line = clean_text(line).lower().strip()
    if not line or len(line) < 2: return None

    quantity = 1
    item_clean = line

    # 2. UNIVERSAL SEPARATOR LOGIC
    # Now that "want to sell" is stripped by the caller, '^' will correctly hit the number
    match_start = re.match(r'^(\d+)\s*[xX\-\.]?\s*(.*)', line)
    match_end = re.search(r'(.*)\s+[xX\-\.]?\s*(\d+)$', line)

    if match_start:
        quantity = int(match_start.group(1))
        item_clean = match_start.group(2).strip()
    elif match_end:
        quantity = int(match_end.group(2))
        item_clean = match_end.group(1).strip()
    
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

    # 6. STOP IF ALIASED
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

def process_text_block(input_text, price_dict_buy, price_dict_sell):
    """
    Process a block of text and intelligently distribute items to Buy or Sell lists.
    """
    # 1. Normalize commas to newlines
    normalized_text = input_text.replace(',', '\n')
    lines = normalized_text.split('\n')
    
    new_payout_items = []
    new_cost_items = []
    
    for line in lines:
        if not line.strip(): continue
        
        # 2. Detect Intent & Clean Prefixes ("Want to sell 5x..." -> Intent: SELL, Text: "5x...")
        intent, cleaned_line = detect_intent_and_clean(line)
        
        # 3. Decide which DB to use based on Intent
        # If Player Sells (Payout) -> Use WE_BUY prices
        # If Player Buys (Cost)   -> Use WE_SELL prices
        
        # Default to Payout if Neutral (assuming user pasted in Payout tab)
        target_list = "PAYOUT" 
        
        if intent == "PLAYER_BUYS":
            target_list = "COST"
            parsed = smart_parse_line(cleaned_line, price_dict_sell)
        else:
            # PLAYER_SELLS or NEUTRAL
            parsed = smart_parse_line(cleaned_line, price_dict_buy)
            
        if parsed:
            if target_list == "COST":
                new_cost_items.append(parsed)
            else:
                new_payout_items.append(parsed)
                
    return new_payout_items, new_cost_items

def render_result_tables():
    # Render PAYOUT Table
    st.subheader("💰 Payout (We Buy)")
    if 'buy_df' in st.session_state and not st.session_state.buy_df.empty:
        df = st.session_state.buy_df
        if "Item" in df.columns:
            fmt_df = df.copy()
            fmt_df["Unit Price"] = fmt_df["Unit Price"].apply(lambda x: f"{x:,}")
            fmt_df["Total"] = fmt_df["Total"].apply(lambda x: f"{x:,}")
            st.table(fmt_df[["Item", "Qty", "Unit Price", "Total"]])
            st.success(f"### Total Payout: {df['Total'].sum():,}")
    else:
        st.info("No Payout items yet.")

    st.markdown("---") # Divider

    # Render COST Table
    st.subheader("🛒 Cost (We Sell)")
    if 'sell_df' in st.session_state and not st.session_state.sell_df.empty:
        df = st.session_state.sell_df
        if "Item" in df.columns:
            fmt_df = df.copy()
            fmt_df["Unit Price"] = fmt_df["Unit Price"].apply(lambda x: f"{x:,}")
            fmt_df["Total"] = fmt_df["Total"].apply(lambda x: f"{x:,}")
            st.table(fmt_df[["Item", "Qty", "Unit Price", "Total"]])
            st.error(f"### Total Due: {df['Total'].sum():,}") # Red box for cost
    else:
        st.info("No Cost items yet.")

def clear_state():
    st.session_state.buy_df = pd.DataFrame()
    st.session_state.sell_df = pd.DataFrame()
    st.session_state["master_input"] = ""

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

    # --- MAIN INPUT AREA (The Brain) ---
    st.markdown("### 📜 Smart Trade Processor")
    st.markdown("Paste your **entire ticket** here. The AI will sort buys vs sells automatically.")
    
    input_text = st.text_area("Paste Chat Log / Ticket:", height=200, key="master_input")
    
    if st.button("🚀 Process Ticket"):
        payouts, costs = process_text_block(input_text, WE_BUY, WE_SELL)
        
        if payouts:
            st.session_state.buy_df = pd.DataFrame(payouts)
        else:
            st.session_state.buy_df = pd.DataFrame() # Clear if empty
            
        if costs:
            st.session_state.sell_df = pd.DataFrame(costs)
        else:
             st.session_state.sell_df = pd.DataFrame() # Clear if empty

    # --- DISPLAY RESULTS ---
    render_result_tables()

    st.button("🗑️ Clear All", on_click=clear_state)

if __name__ == "__main__":
    main()
