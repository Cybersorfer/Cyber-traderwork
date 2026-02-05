import streamlit as st
import re
import json
import pandas as pd
from datetime import date
from thefuzz import process

# --- PAGE CONFIG ---
st.set_page_config(page_title="Cyber Trader Suite", page_icon="⚖️", layout="wide")

# --- ALIAS LIST (The "Translator") ---
# This forces the app to recognize specific short names.
# "user typed": "EXACT KEY IN PRICES.JSON"
ALIASES = {
    "lar": "LAR",        # <--- THIS LINE FIXES YOUR BUG. It forces "lar" to look for "LAR".
    "m16": "M16",        # Forces "m16" to look for "M16"
    "m4": "M4",
    "ak": "KA-74",       # Example: maps "ak" to "KA-74"
    "vs": "VSS"
}

# --- CUSTOM CSS FOR CYBER/NIGHT MODE ---
def set_theme():
    st.markdown("""
    <style>
        .stApp { background-color: #0E1117; color: #FAFAFA; }
        section[data-testid="stSidebar"] { background-color: #262730; }
        section[data-testid="stSidebar"] * { color: #FAFAFA !important; }
        .stTextArea label, .stTextInput label, .stNumberInput label, .stDateInput label, .stCheckbox label {
            color: #E0E0E0 !important; font-size: 1rem; font-weight: bold;
        }
        .stTextArea textarea, .stTextInput input, .stNumberInput input, .stDateInput input {
            background-color: #1E1E1E !important; color: #00FF00 !important;
            border: 1px solid #4CAF50; caret-color: #00FF00;
        }
        .stButton>button {
            color: #FAFAFA; background-color: #262730; border: 1px solid #4CAF50; transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #4CAF50; color: #000000; box-shadow: 0 0 10px #4CAF50;
        }
        [data-testid="stMetricValue"], [data-testid="stMetricLabel"] { color: #4CAF50 !important; }
        thead tr th { color: #FAFAFA !important; background-color: #262730 !important; }
        tbody tr td { color: #E0E0E0 !important; }
        div[data-baseweb="calendar"] { background-color: #262730 !important; }
        div[data-baseweb="calendar"] div { color: #FAFAFA !important; }
        div[data-baseweb="calendar"] button:hover { background-color: #4CAF50 !important; color: #000000 !important; }
        div[aria-selected="true"] { background-color: #4CAF50 !important; color: #000000 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.header("🔥 Item of the Week")
special_item_active = st.sidebar.checkbox("Enable Special Price")
special_name = st.sidebar.text_input("Item Name (e.g. Gas Stove)")
special_price_input = st.sidebar.text_input("Special Price", value="0")
try:
    special_price = int(special_price_input)
except ValueError:
    special_price = 0
expiry_date = st.sidebar.date_input("Offer Ends On", min_value=date.today())
if st.sidebar.button("🔄 Update Promo"):
    st.rerun()

is_expired = date.today() > expiry_date
if special_item_active and is_expired:
    st.sidebar.error(f"⚠️ Offer expired on {expiry_date}")

# --- LOGIC ---
def load_prices():
    try:
        with open('prices.json', 'r') as f:
            return json.load(f)
    except Exception:
        return {"WE_BUY": {}, "WE_SELL": {}}

def smart_parse_line(line, price_dict):
    line = line.lower().strip()
    if not line or len(line) < 2: return None

    # 1. QUANTITY
    quantity = 1
    item_clean = line
    match_start = re.match(r'^(\d+)\s*[:-x\s]?\s*', line)
    match_end = re.search(r'\s*[:-x\s]?\s*(\d+)$', line)

    if match_start:
        quantity = int(match_start.group(1))
        item_clean = line[match_start.end():] 
    elif match_end:
        quantity = int(match_end.group(1))
        item_clean = line[:match_end.start()]

    item_clean = item_clean.replace('-', ' ').strip()
    
    # 2. CHECK ALIASES (The Translator)
    # This translates "lar" to "LAR" before we even look at the database.
    if item_clean in ALIASES:
        item_clean = ALIASES[item_clean].lower()

    # 3. SPECIAL ITEM
    if special_item_active and not is_expired and special_name:
        if special_name.lower() in item_clean:
             return {"Item": f"🔥 {special_name} (SPECIAL)", "Qty": quantity, "Unit Price": special_price, "Total": quantity * special_price}

    # 4. IGNORE RULE
    if "item of the week" in line: return None
    if not item_clean: return None

    # 5. EXACT MATCH
    # Since Alias converted it to "lar", and "LAR" is in your JSON, this will match.
    exact_map = {k.lower(): k for k in price_dict}
    if item_clean in exact_map:
        real_key = exact_map[item_clean]
        return {"Item": real_key, "Qty": quantity, "Unit Price": price_dict[real_key], "Total": quantity * price_dict[real_key]}

    # 6. FUZZY MATCH (With Safety Guard)
    choices = list(price_dict.keys())
    if not choices: return None
    match, score = process.extractOne(item_clean, choices)
    
    # GUARD: If input is short (<=4 chars), it MUST be inside the match name.
    # "LAR" is not inside "Bear Pelt", so it gets rejected here if the alias/exact match failed.
    if len(item_clean) <= 3:
        if item_clean not in match.lower():
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
        formatted_df = df.copy()
        formatted_df["Unit Price"] = formatted_df["Unit Price"].apply(lambda x: f"{x:,}")
        formatted_df["Total"] = formatted_df["Total"].apply(lambda x: f"{x:,}")
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
    if special_item_active and not is_expired and special_name:
        st.info(f"🔥 **ACTIVE PROMO:** {special_name} @ {special_price:,} until {expiry_date}")

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

