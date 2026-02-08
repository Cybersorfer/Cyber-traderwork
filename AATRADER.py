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

# --- GENERIC CATEGORIES (Fallback Prices) ---
GENERIC_PRICES = {
    "Select Category...": 0,
    "All Other Bags/sacks ($3,000)": 3000,
    "All Other Shoes ($1,000)": 1000,
    "All Other Boots ($2,000)": 2000,
    "All Other Hats and masks ($1,000)": 1000,
    "All other pants ($2,000)": 2000,
    "All other tops ($3,000)": 3000,
    "All Melee Weapons ($4,000)": 4000,
    "Buttstock/Handguard/Bayonets ($2,000)": 2000,
    "All other unlisted mags ($3,000)": 3000,
    "All non-magnifying scopes ($3,000)": 3000,
    "All other unlisted guns ($12,000)": 12000,
    "All Other Seed Packs ($1,000)": 1000
}

# --- TIMEZONE CONFIG (PST LOCK) ---
def get_pst_now():
    pst = pytz.timezone('US/Pacific')
    return datetime.now(pst)

def get_pst_today():
    return get_pst_now().date()

# --- ALIAS LIST ---
# Note: You don't need to add plurals here anymore (e.g. "nails" matches "nail box" automatically via logic)
ALIASES = {
    # Weapons & Ammo
    "lar": "LAR",
    "m16": "M16-A2",     
    "m4": "M4-A1",      
    "ak": "KA-74",      
    "vs": "VSS",
    "vs89": "VS-89",      
    "weed": "cannabis seeds",
    "cannabis seed": "cannabis seeds",
    "nails": "Nail Box",
    "bolts": "Bolts (stack of 5)",
    "9v": "9V Battery",
    "electronic repair kit": "Electronic Repair Kit",

    # --- MAGNIFYING SCOPES ($5,000) ---
    "4x32 scopes": "All magnifying scopes",
    "4x32 scope": "All magnifying scopes",
    "4x32": "All magnifying scopes",
    "hunting scope": "All magnifying scopes",
    "hunting scope(4x-12x)": "All magnifying scopes",
    "marksman scope": "All magnifying scopes",
    "marksman scope(3x-9x)": "All magnifying scopes",
    "pso-1 scope": "All magnifying scopes",
    "pso-1": "All magnifying scopes",
    "pso-1-1 scope": "All magnifying scopes",
    "pso-1-1": "All magnifying scopes",
    "pso-6 scope": "All magnifying scopes",
    "pso-6": "All magnifying scopes",
    "atog 6x48 scope": "All magnifying scopes",
    "atog 6x48": "All magnifying scopes",
    "atog 4x32 scope": "All magnifying scopes",
    "atog 4x32": "All magnifying scopes",
    "pu scope": "All magnifying scopes",
    "pu": "All magnifying scopes",
    "c-1 scope": "All magnifying scopes",
    "c-1": "All magnifying scopes",
    "pistol scope": "All magnifying scopes",
    "1pn51 scope": "All magnifying scopes",
    "1pn51": "All magnifying scopes",
    "kazuar": "All magnifying scopes",
    "starlight": "All magnifying scopes",

    # --- NON-MAGNIFYING SCOPES ($3,000) ---
    "rvn": "All non-magnifying scopes",
    "rvn sight": "All non-magnifying scopes",
    "kobra": "All non-magnifying scopes",
    "kobra sight": "All non-magnifying scopes",
    "m68": "All non-magnifying scopes",
    "comp m4": "All non-magnifying scopes",
    "baraka": "All non-magnifying scopes",
    "baraka sights": "All non-magnifying scopes",
    "reflex": "All non-magnifying scopes",
    "reflex sight": "All non-magnifying scopes",
    "okp-7": "All non-magnifying scopes",
    "okp": "All non-magnifying scopes",
    "red dot": "All non-magnifying scopes",
    "collimator": "All non-magnifying scopes",
    
    # Tents & Storage
    "large tents": "Large Tent",
    "medium tent": "Medium Tent",
    "canopy tent": "Canopy Tent",
    "sea chests": "Seachest",
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
        
        /* Missing Item Box */
        .missing-row {
            background-color: #331111;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 5px;
            border-left: 5px solid #FF4444;
            display: flex;
            align-items: center;
        }
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

# --- NEW SMART PARSING LOGIC ---

def simple_pluralize(word):
    """Simple logic to generate basic plurals for the index."""
    word = word.lower().strip()
    if word.endswith('s'):
        return word # Already looks plural
    if word.endswith('y'):
        return word[:-1] + "ies" # Battery -> Batteries
    if word.endswith('x') or word.endswith('ch') or word.endswith('sh'):
        return word + "es" # Box -> Boxes
    return word + "s" # Gun -> Guns

@st.cache_data
def build_search_index(price_dict, aliases):
    """
    Creates a massive lookup dictionary:
    { "eggs": "Egg", "egg": "Egg", "m4": "M4-A1", "m4s": "M4-A1", ... }
    """
    index = {}
    
    # 1. Add Manual Aliases (and their plurals)
    for alias, real_name in aliases.items():
        clean_alias = alias.lower()
        index[clean_alias] = real_name
        index[simple_pluralize(clean_alias)] = real_name

    # 2. Add Database Items (and their plurals)
    for real_name in price_dict.keys():
        clean_name = str(real_name).lower()
        
        # Add exact name
        index[clean_name] = real_name
        
        # Add plural version
        index[simple_pluralize(clean_name)] = real_name
        
        # Add version without parentheses (e.g., "burlap strips (2)" -> "burlap strips")
        no_variant = re.sub(r'\(.*?\)', '', clean_name).strip()
        if no_variant:
            index[no_variant] = real_name
            index[simple_pluralize(no_variant)] = real_name

    return index

def extract_from_chunk(text, search_index):
    """
    Scans a text chunk for a known item in the index.
    Ignores garbage words. Finds the number closest to the match.
    """
    # 1. Find Quantity (default to 1)
    # This regex finds the first number in the chunk
    qty_match = re.search(r'(\d+)', text)
    quantity = int(qty_match.group(1)) if qty_match else 1
    
    # 2. Normalize Text for searching
    text_clean = text.lower()
    
    # 3. EXACT / KEYWORD SEARCH
    # We sort keys by length (descending) so we match "Large Tent" before "Tent"
    sorted_keys = sorted(search_index.keys(), key=len, reverse=True)
    
    # Scan for keywords
    for key in sorted_keys:
        # \b ensures we don't match "apple" inside "pineapple"
        # We escape key to handle parentheses in regex
        if re.search(r'\b' + re.escape(key) + r'\b', text_clean):
            real_name = search_index[key]
            return real_name, quantity, True

    return text, quantity, False

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
    # 1. Build Index (Combine Buy/Sell keys so we recognize items regardless of context)
    combined_keys = {**price_dict_buy, **price_dict_sell} 
    search_index = build_search_index(combined_keys, ALIASES)

    raw_lines = input_text.split('\n')
    new_payout_items = []   # We Buy
    new_cost_items = []     # We Sell (Trader Sells)
    new_missing_items = []
    
    # Default mode
    current_mode = "PAYOUT" 
    
    for raw_line in raw_lines:
        if not raw_line.strip(): continue
        
        # Check for Mode Switching
        new_mode, keyword = check_mode_switch(raw_line)
        if new_mode:
            current_mode = new_mode
            line_content = re.sub(keyword, "", raw_line, flags=re.IGNORECASE)
        else:
            line_content = raw_line

        # Split by comma to handle lists like "5 eggs, 2 bacon"
        comma_parts = line_content.split(',')
        
        for part in comma_parts:
            part = part.strip()
            if not part: continue
            
            # --- NEW EXTRACTION LOGIC ---
            item_name, qty, found = extract_from_chunk(part, search_index)
            
            # Determine Price & Source
            price = 0
            if found:
                # Check Promo First
                if promo_info.get("active") and promo_info.get("name").lower() in item_name.lower():
                     price = promo_info.get("price")
                     item_name = f"🔥 {promo_info.get('name')}"
                else:
                    # Look up price based on current mode
                    if current_mode == "COST":
                        price = price_dict_sell.get(item_name, 0)
                    else:
                        price = price_dict_buy.get(item_name, 0)

            # Construct Result Object
            entry = {
                "Item": item_name,
                "Qty": qty,
                "Unit Price": price,
                "Total": qty * price,
                "Found": found,
                "Type": current_mode
            }

            if found and price > 0:
                if current_mode == "COST":
                    new_cost_items.append(entry)
                else:
                    new_payout_items.append(entry)
            else:
                # Either not found, or found but price is 0 (mismatch in buy/sell lists)
                new_missing_items.append(entry)
                
    return new_payout_items, new_cost_items, new_missing_items

def render_result_tables():
    # --- CALCULATE MANUAL RESOLUTIONS ---
    resolved_payout = 0
    resolved_cost = 0

    if 'missing_df' in st.session_state and not st.session_state.missing_df.empty:
        st.warning("⚠️ **Items Not Found - Manual Resolution Needed:**")
        st.markdown("Select a category for each missing item to add it to the total.")
        
        m_df = st.session_state.missing_df
        
        # Iterate through missing items to create selectors
        for index, row in m_df.iterrows():
            c1, c2, c3 = st.columns([3, 1, 3])
            with c1:
                st.write(f"❌ **{row['Item']}** (x{row['Qty']})")
            with c2:
                st.caption(f"Type: {row['Type']}")
            with c3:
                # Unique key per row so they don't conflict
                cat_key = f"cat_{index}_{row['Item']}"
                selected_cat = st.selectbox(
                    "Assign Category:", 
                    options=GENERIC_PRICES.keys(), 
                    key=cat_key,
                    label_visibility="collapsed"
                )
                
                # Math Logic
                price = GENERIC_PRICES[selected_cat]
                line_total = price * row['Qty']
                
                # Add to the correct running total
                if line_total > 0:
                    if row['Type'] == "PAYOUT":
                        resolved_payout += line_total
                    else:
                        resolved_cost += line_total
                    st.success(f"+ ${line_total:,}")
        
        st.markdown("---")

    # --- PAYOUT SECTION ---
    st.subheader("💰 Payout (We Buy)")
    payout_db_total = 0
    if 'buy_df' in st.session_state and not st.session_state.buy_df.empty:
        df = st.session_state.buy_df
        if "Item" in df.columns:
            fmt_df = df.copy()
            fmt_df["Unit Price"] = fmt_df["Unit Price"].apply(lambda x: f"{x:,}")
            fmt_df["Total"] = fmt_df["Total"].apply(lambda x: f"{x:,}")
            st.table(fmt_df[["Item", "Qty", "Unit Price", "Total"]])
            payout_db_total = df['Total'].sum()
    else:
        st.info("No Payout items found in database.")

    # FINAL PAYOUT MATH
    final_payout = payout_db_total + resolved_payout
    if resolved_payout > 0:
        st.success(f"### Total: ${payout_db_total:,} (DB) + ${resolved_payout:,} (Resolved) = ${final_payout:,}")
    else:
        st.success(f"### Total Payout: ${final_payout:,}")

    st.markdown("---")

    # --- COST SECTION ---
    st.subheader("🛒 Cost (We Sell)")
    cost_db_total = 0
    if 'sell_df' in st.session_state and not st.session_state.sell_df.empty:
        df = st.session_state.sell_df
        if "Item" in df.columns:
            fmt_df = df.copy()
            fmt_df["Unit Price"] = fmt_df["Unit Price"].apply(lambda x: f"{x:,}")
            fmt_df["Total"] = fmt_df["Total"].apply(lambda x: f"{x:,}")
            st.table(fmt_df[["Item", "Qty", "Unit Price", "Total"]])
            cost_db_total = df['Total'].sum()
    else:
        st.info("No Cost items found in database.")

    # FINAL COST MATH
    final_cost = cost_db_total + resolved_cost
    if resolved_cost > 0:
        st.error(f"### Total: ${cost_db_total:,} (DB) + ${resolved_cost:,} (Resolved) = ${final_cost:,}")
    else:
        st.error(f"### Total Due: ${final_cost:,}")

def clear_state():
    st.session_state.buy_df = pd.DataFrame()
    st.session_state.sell_df = pd.DataFrame()
    st.session_state.missing_df = pd.DataFrame()
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
    if 'missing_df' not in st.session_state: st.session_state.missing_df = pd.DataFrame()

    st.markdown("### 📜 Smart Trade Processor")
    st.markdown(f"Paste your **{selected_map} ticket** here. The AI will sort buys vs sells automatically.")
    
    input_text = st.text_area("Paste Chat Log / Ticket:", height=200, key="master_input")
    
    if st.button("🚀 Process Ticket"):
        payouts, costs, missing = process_text_block(input_text, WE_BUY, WE_SELL, promo_info_package)
        st.session_state.buy_df = pd.DataFrame(payouts) if payouts else pd.DataFrame()
        st.session_state.sell_df = pd.DataFrame(costs) if costs else pd.DataFrame()
        st.session_state.missing_df = pd.DataFrame(missing) if missing else pd.DataFrame()

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
