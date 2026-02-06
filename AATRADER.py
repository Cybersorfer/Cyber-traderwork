import streamlit as st
import re
import json
import os
import pandas as pd
import pytz 
from datetime import datetime, date
from thefuzz import process

# --- PAGE CONFIG ---
st.set_page_config(page_title="Cyber Economy Suite", page_icon="🌍", layout="wide")

# --- MAP CONFIGURATION ---
MAPS = {
    "Chernarus": "prices_chernarus.json",
    "Livonia": "prices_livonia.json",
    "Sakhal": "prices_sakhal.json"
}
PROMO_FILE = 'promo.json'

# --- TIMEZONE CONFIG (PST LOCK) ---
def get_pst_now():
    pst = pytz.timezone('US/Pacific')
    return datetime.now(pst)

def get_pst_today():
    return get_pst_now().date()

# --- ALIAS LIST ---
# Maps user inputs (lowercase) to the EXACT name in your JSON
ALIASES = {
    "lar": "LAR",
    "lars": "LAR",       
    "m16": "M16-A2",     
    "m4": "M4-A1",      
    "ak": "KA-74",      
    "vs": "VSS",
    "vs89": "VS-89",      
    "weed": "cannabis seeds",
    "seeds": "cannabis seeds",
    "cannabis seed": "cannabis seeds",
    "nails": "Nail Box",
    "bolts": "Bolts (stack of 5)",
    "9v": "9V Battery",
    "electronic repair kit": "Electronic Repair Kit",
    # Tents & Storage
    "large tents": "Large Tent",
    "large tent": "Large Tent",
    "medium tent": "Medium Tent",
    "canopy tent": "Canopy Tent",
    "sea chests": "Seachest",
    "sea chest": "Seachest",
    "seachests": "Seachest",
    "blue barrel": "Barrel",
    "green barrel": "Barrel",
    "red barrel": "Barrel",
    "yellow barrel": "Barrel",
    # Construction
    "construction lights": "Construction Light",
    "cable reels": "Cable Reel",
    "generator": "Generator",
    "battery charger": "Battery Charger", 
    "santa hats": "Santa Hat",
    "santa beard": "Santa Beard"
}

# --- JUNK WORD REMOVER ---
# Words to strip out entirely
FILLERS = [
    "pack of", "packs of", "box of", "can of",
    "cr550", "item of the week", "for the",
    "stored in", "inside", "would like to",
    "hi i'd like to", "please", "thank you", "thanks"
]

# --- VARIANT STRIPPER ---
# Words to remove if the item isn't found (Colors, variants)
VARIANTS = [
    "(black)", "(green)", "(tan)", "(camo)", "(winter)", "(summer)", 
    "(pink)", "(blue)", "(red)", "(yellow)", "(white)", "(grey)", "(gray)",
    "black", "green", "tan", "camo", "winter", "summer", "pink", "blue", "red", "yellow", "white"
]

# --- CUSTOM CSS ---
def set_theme():
    st.markdown("""
    <style>
        .stApp { background-color: #0E1117; color: #E0E0E0; }
        section[data-testid="stSidebar"] { background-color: #262730; }
        section[data-testid="stSidebar"] * { color: #FAFAFA !important; }
        .stTextArea label, .stTextInput label, .stNumberInput label, .stDateInput label, .stCheckbox label, .stSelectbox label {
            color: #B0B0B0 !important; font-size: 1rem; font-weight: bold;
        }
        .stTextArea textarea, .stTextInput input, .stNumberInput input {
            background-color: #1E1E1E !important; 
            color: #00FF00 !important;
            border: 1px solid #4CAF50; 
            caret-color: #00FF00;
        }
        input[type="date"] {
            background-color: #1E1E1E !important;
            color: #00FF00 !important;
            filter: invert(0) !important;
            border: 1px solid #4CAF50 !important;
        }
        div[data-baseweb="input"] {
            background-color: #1E1E1E !important;
            border-color: #4CAF50 !important;
        }
        div[data-baseweb="select"] > div {
            background-color: #1E1E1E !important;
            color: #00FF00 !important;
            border-color: #4CAF50 !important;
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

# --- SAVE/LOAD FUNCTIONS ---
def load_prices(map_name):
    file_path = MAPS.get(map_name, "prices_chernarus.json")
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception:
        return {"WE_BUY": {}, "TRADER_SELLS": {}}

def load_all_promos():
    if os.path.exists(PROMO_FILE):
        try:
            with open(PROMO_FILE, 'r') as f: return json.load(f)
        except: pass
    return {}

def save_all_promos(data):
    with open(PROMO_FILE, 'w') as f: json.dump(data, f)

def clean_noise(text):
    # 1. Remove Dollar amounts (e.g. $25,000, $500)
    text = re.sub(r'\$[\d,]+', '', text)
    # 2. Remove equations (e.g. = $50,000)
    text = re.sub(r'=\s*[\d,]+', '', text)
    # 3. Remove "Grand Total" lines
    if "total" in text.lower(): return ""
    # 4. Standard clean (Keep () and - and . for items like "Bolts (Stack of 5)")
    return re.sub(r'[^a-zA-Z0-9\-\.\(\) ]', '', text)

def strip_variants(text):
    # Removes (Black), (Winter), etc.
    text_lower = text.lower()
    for v in VARIANTS:
        text_lower = text_lower.replace(v, "")
    # Remove empty parens ()
    text_lower = text_lower.replace("()", "").strip()
    return text_lower

def smart_parse_line(line, price_dict, promo_info):
    if "locker code" in line.lower() or "combo" in line.lower(): return None

    # Step 1: Basic Clean
    line = clean_noise(line).strip()
    if not line or len(line) < 2: return None

    quantity = 1
    item_clean = line

    # Extraction Logic (Qty + Item)
    match_start = re.match(r'^(\d+)\s*[xX\-\.]?\s*(.*)', line)
    match_end = re.search(r'(.*)\s+[xX\-\.]?\s*(\d+)$', line)

    if match_start:
        quantity = int(match_start.group(1))
        item_clean = match_start.group(2).strip()
    elif match_end:
        quantity = int(match_end.group(2))
        item_clean = match_end.group(1).strip()

    # Step 2: Remove Filler Words
    for filler in FILLERS:
        item_clean = item_clean.replace(filler, "").strip()

    # Step 3: Check Aliases (First Pass)
    if item_clean.lower() in ALIASES:
        item_clean = ALIASES[item_clean.lower()]

    # --- MATCHING LOGIC ---
    
    # 1. PROMO MATCH
    s_active = promo_info.get("active", False)
    s_name = promo_info.get("name", "")
    s_price = promo_info.get("price", 0)
    s_expiry = promo_info.get("expiry_date", get_pst_today())

    if (s_name and s_name.lower() in item_clean.lower()):
        if s_active and get_pst_today() <= s_expiry:
             return {"Item": f"🔥 {s_name}", "Qty": quantity, "Unit Price": s_price, "Total": quantity * s_price}

    exact_map = {str(k).lower(): str(k) for k in price_dict if k}
    
    # 2. EXACT MATCH (Try 1: As Is)
    # Allows "Bolts (Stack of 5)" to match if it exists
    if item_clean.lower() in exact_map:
        real_key = exact_map[item_clean.lower()]
        return {"Item": real_key, "Qty": quantity, "Unit Price": price_dict[real_key], "Total": quantity * price_dict[real_key]}

    # 3. VARIANT STRIP MATCH (Try 2: Remove Colors)
    # Converts "Plate Carrier (Black)" -> "Plate Carrier"
    item_no_variant = strip_variants(item_clean)
    if item_no_variant in exact_map:
        real_key = exact_map[item_no_variant]
        return {"Item": real_key, "Qty": quantity, "Unit Price": price_dict[real_key], "Total": quantity * price_dict[real_key]}

    # 4. FUZZY MATCH
    choices = [str(k) for k in price_dict.keys() if k]
    if not choices: return None
    
    # Try fuzzy on the CLEAN version (No Variants)
    match, score = process.extractOne(item_no_variant, choices)
    
    if score < 85: return None
    # Short word guard
    if len(item_no_variant) <= 4 and item_no_variant not in match.lower(): return None 
    
    return {"Item": match, "Qty": quantity, "Unit Price": price_dict[match], "Total": quantity * price_dict[match]}

def check_mode_switch(line):
    line_lower = line.lower()
    buy_keywords = [
        "want to buy", "buying", "wtb", "want to order", "ordering", "need", 
        "would like to buy", "would like to order", "like to buy", "looking to buy"
    ]
    for kw in buy_keywords:
        if kw in line_lower: return "COST", kw
        
    sell_keywords = [
        "want to sell", "selling", "wts", "i have", "have", "would like to sell",
        "like to sell", "looking to sell"
    ]
    for kw in sell_keywords:
        if kw in line_lower: return "PAYOUT", kw
        
    return None, None

def process_text_block(input_text, price_dict_buy, price_dict_sell, promo_info):
    raw_lines = input_text.split('\n')
    new_payout_items = []
    new_cost_items = []
    current_mode = "PAYOUT" 
    
    for raw_line in raw_lines:
        if not raw_line.strip(): continue
        
        # 1. Check for Mode Switch
        new_mode, keyword = check_mode_switch(raw_line)
        if new_mode:
            current_mode = new_mode
            line_content = re.sub(keyword, "", raw_line, flags=re.IGNORECASE)
        else:
            line_content = raw_line

        # 2. Split by commas
        comma_parts = line_content.split(',')
        
        for part in comma_parts:
            part = part.strip()
            if not part: continue
            
            if current_mode == "COST":
                parsed = smart_parse_line(part, price_dict_sell, promo_info)
                if parsed: new_cost_items.append(parsed)
            else:
                parsed = smart_parse_line(part, price_dict_buy, promo_info)
                if parsed: new_payout_items.append(parsed)
                
    return new_payout_items, new_cost_items

def render_result_tables():
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
        st.info("No Payout items.")

    st.markdown("---")

    st.subheader("🛒 Cost (We Sell)")
    if 'sell_df' in st.session_state and not st.session_state.sell_df.empty:
        df = st.session_state.sell_df
        if "Item" in df.columns:
            fmt_df = df.copy()
            fmt_df["Unit Price"] = fmt_df["Unit Price"].apply(lambda x: f"{x:,}")
            fmt_df["Total"] = fmt_df["Total"].apply(lambda x: f"{x:,}")
            st.table(fmt_df[["Item", "Qty", "Unit Price", "Total"]])
            st.error(f"### Total Due: {df['Total'].sum():,}")
    else:
        st.info("No Cost items.")

def clear_state():
    st.session_state.buy_df = pd.DataFrame()
    st.session_state.sell_df = pd.DataFrame()
    st.session_state["master_input"] = ""

def main():
    set_theme()
    
    st.sidebar.title("🌍 Map Selector")
    selected_map = st.sidebar.selectbox("Select Server Map:", list(MAPS.keys()))
    st.title(f"⚖️ {selected_map} Economy Suite")
    
    all_promos = load_all_promos()
    map_promo = all_promos.get(selected_map, {})
    
    st.sidebar.header(f"🔥 {selected_map} Item of Week")
    
    special_item_active = st.sidebar.checkbox("Enable Special Price", value=map_promo.get("active", False))
    special_name = st.sidebar.text_input("Item Name (e.g. Gas Stove)", value=map_promo.get("name", ""))
    special_price_val = st.sidebar.text_input("Special Price", value=str(map_promo.get("price", 0)))
    
    saved_date_str = map_promo.get("expiry", str(get_pst_today()))
    try: default_date = date.fromisoformat(saved_date_str)
    except: default_date = get_pst_today()
        
    expiry_date = st.sidebar.date_input("Offer Ends On", value=default_date, min_value=get_pst_today())
    
    try: special_price = int(special_price_val)
    except: special_price = 0

    pst_time_str = get_pst_now().strftime("%I:%M %p")
    st.sidebar.markdown(f"""
        <div style="margin-bottom: 10px; margin-top: 10px;">
            <b style="color: #B0B0B0; font-size: 1rem;">🕒 Server Time(PST):</b> 
            <br>
            <span style="color: #00FF00; font-size: 1.2rem; font-weight: bold;">{pst_time_str}</span>
        </div>
        """, unsafe_allow_html=True)
    
    if st.sidebar.button("🔄 Update Promo"):
        all_promos[selected_map] = {
            "active": special_item_active,
            "name": special_name,
            "price": special_price,
            "expiry": str(expiry_date)
        }
        save_all_promos(all_promos)
        st.success(f"Promo for {selected_map} Saved!")
        st.rerun()

    promo_info_package = {
        "active": special_item_active,
        "name": special_name,
        "price": special_price,
        "expiry_date": expiry_date
    }

    data = load_prices(selected_map)
    WE_BUY = data.get("WE_BUY", {})
    WE_SELL = data.get("TRADER_SELLS", {})

    if 'buy_df' not in st.session_state: st.session_state.buy_df = pd.DataFrame()
    if 'sell_df' not in st.session_state: st.session_state.sell_df = pd.DataFrame()

    st.markdown("### 📜 Smart Trade Processor")
    st.markdown(f"Paste your **{selected_map} ticket** here. The AI will sort buys vs sells automatically.")
    
    input_text = st.text_area("Paste Chat Log / Ticket:", height=200, key="master_input")
    
    if st.button("🚀 Process Ticket"):
        payouts, costs = process_text_block(input_text, WE_BUY, WE_SELL, promo_info_package)
        st.session_state.buy_df = pd.DataFrame(payouts) if payouts else pd.DataFrame()
        st.session_state.sell_df = pd.DataFrame(costs) if costs else pd.DataFrame()

    render_result_tables()
    
    with st.expander("🕵️ Debug: Search Price Database"):
        st.write(f"Searching database for: **{selected_map}**")
        search_q = st.text_input("Search Item Name")
        if search_q:
            hits_buy = [k for k in WE_BUY.keys() if search_q.lower() in str(k).lower()]
            hits_sell = [k for k in WE_SELL.keys() if search_q.lower() in str(k).lower()]
            if hits_buy: st.write(f"**Found in WE BUY:** {hits_buy}")
            if hits_sell: st.write(f"**Found in TRADER SELLS:** {hits_sell}")
            if not hits_buy and not hits_sell: st.warning("Not found in either list.")

    st.button("🗑️ Clear All", on_click=clear_state)

if __name__ == "__main__":
    main()
