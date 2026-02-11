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
    "lower caliber ammo box ($2,000)": 2000,
    "higher Ammo Box ($4,000)": 4000,
    "All Other Seed Packs ($1,000)": 1000,
    "FREE ($0)": 0
}

# --- TIMEZONE CONFIG (PST LOCK) ---
def get_pst_now():
    pst = pytz.timezone('US/Pacific')
    return datetime.now(pst)

def get_pst_today():
    return get_pst_now().date()

# --- ALIAS LIST ---
ALIASES = {
    "item of the week": "🔥🔥PROMO_ITEM🔥🔥", 
    "item of week": "🔥🔥PROMO_ITEM🔥🔥",
    "promo item": "🔥🔥PROMO_ITEM🔥🔥",
    "prn": "Pen", 
    "ptn": "Pen",
    "pm": "Pen",
    "Pencil": "Pen",
    "zagorty": "Zagorky",
    "zagorky snacks": "Zagorky",
    "unknown food": "Unknown Food Can",
    "unknown can": "Unknown Food Can",
    "sharpening stone": "Whetstone",
    "sharpening stones": "Whetstone",
    "anniversary tshirt": "10th Anniversary Tshirt",
    "anniversary t-shirt": "10th Anniversary Tshirt",
    "30th anniversary tshirt": "10th Anniversary Tshirt",
    "weed crate full": "wooden crate full of weed(50 dried buds)", 
    "weed crate": "wooden crate full of weed(50 dried buds)", 
    "weed wooden crate": "wooden crate full of weed(50 dried buds)", 
    "crate of weed": "wooden crate full of weed(50 dried buds)",
    "crate full of weed": "wooden crate full of weed(50 dried buds)",
    "seachest full of weed": "seachest full of weed(100 dried buds)",
    "sea chest full of weed": "seachest full of weed(100 dried buds)",    
    "weed seachest full": "seachest full of weed(100 dried buds)",
    "weed seachest": "seachest full of weed(100 dried buds)",
    "weed sea chest full": "seachest full of weed(100 dried buds)",
    "weed sea chest": "seachest full of weed(100 dried buds)",
    "Packs of Smokes": "Cigarettes",
    "Smokes": "Cigarettes", 
    "cigarette pack": "Cigarettes",
    "cigs pack": "Cigarettes",
    "cig": "Cigarettes",
    "ciggies": "Cigarettes",
    "fags": "Cigarettes",
    "butts": "Cigarettes",
    "cancer stick": "Cigarettes",
    "cowboy killer": "Cigarettes",
    "darts": "Cigarettes",
    "POX": "POX Antidote",
    "Antidote": "POX Antidote",
    "Medical Pouch": "First Aid Pouch",
    "Aid Pouch": "First Aid Pouch",
    "Cannabis Seeds": "Cannabis Seed Pack", 
    "Weed Seeds": "Cannabis Seed Pack",
    "weed Seed Pack": "Cannabis Seed Pack",
    "Seed Packs": "All Other Seed Packs",
    "Fertilizer":"Garden Lime",
    "Barbed Wire": "Barb Wire",
    "Barbwire": "Barb Wire",
    "4 Digit Lock": "4-Digit Lock",
    "4 DialLock": "4-Digit Lock",
    "4 Dial Lock": "4-Digit Lock",
    "4-Dial Lock": "4-Digit Lock",
    "4Digit Lock": "4-Digit Lock",
    "4Dial Lock": "4-Digit Lock",
    "Camo Net": "Camo Netting",
    "Cammo Net": "Camo Netting",
    "stacks of sheet metal": "Metal Sheet (stack of 10)",
    "sheet metal": "Metal Sheet (stack of 10)",
    "hard Case": "Protective Case",
    "hardCase": "Protective Case",
    "yellow Case": "Protective Case",
    "other tops":"All other tops",
    "tops":"All other tops",
    "shirt":"All other tops",
    "tshirt":"All other tops",
    "t-shirt":"All other tops",
    "jacket":"All other tops",
    "sweater":"All other tops",
    "upper body":"All other tops",
    "hat":"All Other Hats and masks",
    "mask": "All Other Hats and masks",
    "googles": "All Other Hats and masks",
    "goggles": "All Other Hats and masks",
    "glasses": "All Other Hats and masks",
    "sunglasses": "All Other Hats and masks",
    "pants": "All other pants",
    "Shorts": "All other pants",
    "bottoms": "All other pants",
    "lower body": "All other pants",
    "knife":"All Melee Weapons",
    "machete":"All Melee Weapons",
    "mace": "All Melee Weapons",
    "bat": "All Melee Weapons",
    "fange": "All Melee Weapons",
    "sword": "All Melee Weapons",
    "NVGs": "Night Vision Goggles",
    "NVG": "Night Vision Goggles",
    "Car Wheel": "Car Wheels",
    "Wheels": "Car Wheels",
    "Wheel": "Car Wheels",
    "Hack saw": "Hacksaw",
    "Hecksaw": "Hacksaw",
    "Pick axe": "Pickaxe",
    "Pack axe": "Pickaxe",
    "sharpening stone": "Whetstone",
    "sharping stone": "Whetstone",
    "Field Bag": "Field Backpack",
    "Field pack": "Field Backpack",
    "Field sack": "Field Backpack",
    "Yellow Scarred Helmet": "Yellow Scarred Moto Helmet",  
    "Scarred moto Helmet": "Yellow Scarred Moto Helmet",  
    "Scarred Helmet": "Yellow Scarred Moto Helmet",
    "King helmet": "Yellow Scarred Moto Helmet", 
    "M79": "M79 Grenade Launcher",
    "Savanna": "CR-550 Savanna",
    "CR-550 Savannah": "CR-550 Savanna",
    "savannah": "CR-550 Savanna",
    "vihker": "Vikhr",
    "KA-101": "KA101",
    "lar": "LAR",
    "m16": "M16-A2",     
    "m4": "M4-A1",      
    "ak": "KA-74",      
    "vs": "VSS",
    "vs89": "VS-89",
    "vsd": "VSD",
    "val": "SVAL",
    "weed seeds": "cannabis seeds",
    "cannabis seed": "cannabis seeds",
    "nails": "Nail Box",
    "bolts": "Bolts (stack of 5)",
    "9v": "9V Battery",
    "electronic repair kit": "Electronic Repair Kit",
    "seachests": "Seachest",
    "sea chest": "Seachest",
    "sea chests": "Seachest",
    "blue locker": "Locker",
    "pistol": "All other unlisted guns",
    "rifle": "All other unlisted guns",
    ".22": ".22 LR Ammo Box",
    ".22lr": ".22 LR Ammo Box",
    "5.56": "5.56x45 Ammo Box",
    "5,56": "5.56x45 Ammo Box",
    "5,56x45": "5.56x45 Ammo Box",
    "5.56x45mm": "5.56x45 Ammo Box",
    "5.56x45 mm": "5.56x45 Ammo Box",
    "5.45": "5.45x39 Ammo Box",
    "5,45": "5.45x39 Ammo Box",
    "5,45x39": "5.45x39 Ammo Box",
    "5.45x39 mm": "5.45x39 Ammo Box",
    "5.45x39mm": "5.45x39 Ammo Box",
    "7.62x39": "7.62x39 Ammo Box",
    "7.62x39mm": "7.62x39 Ammo Box",
    "7.62x39 mm": "7.62x39 Ammo Box",
    "7,62x39": "7.62x39 Ammo Box",
    "7.62x54": "7.62x54 Ammo Box",
    "7,62x54": "7.62x54 Ammo Box", 
    "308": ".308 WIN Ammo Box",
    ".308": ".308 WIN Ammo Box",
    "357": ".357 Ammo Box",
    ".357": ".357 Ammo Box",
    "12g": "12ga Ammo Box",
    "12ga": "12ga Ammo Box",
    "9x39": "9x39 Ammo Box",
    "9x39mm": "9x39 Ammo Box",
    "9x39 mm": "9x39 Ammo Box",
    "handgun ammo": "lower caliber ammo box",
    "handgun ammo box": "lower caliber ammo box",
    "shotgun ammo box": "lower caliber ammo box",
    "shotgun ammo": "lower caliber ammo box",
    "low caliber": "lower caliber ammo box",
    "low ammo": "lower caliber ammo box",
    ".380 ammo": "lower caliber ammo box",
    ".380 acp": "lower caliber ammo box",
    ".380 acp ammo": "lower caliber ammo box",
    ".380acp": "lower caliber ammo box",
    ".45 ACP": ".45 ACP Ammo Box",
    ".45ACP": ".45 ACP Ammo Box", 
    ".45": ".45 ACP Ammo Box",
    "rifle ammo": "higher Ammo Box",
    "rifle ammo box": "higher Ammo Box",
    "high caliber ammo": "higher Ammo Box",
    "high caliber": "higher Ammo Box",
    "higher caliber ammo": "higher Ammo Box",
    "high ammo": "higher Ammo Box",
    "4x32 scopes": "All magnifying scopes",
    "4x32 scope": "All magnifying scopes",
    "hunting scope": "All magnifying scopes",
    "pso-1": "All magnifying scopes",
    "pso-1-1": "All magnifying scopes",
    "pu scope": "All magnifying scopes",
    "kazuar": "All magnifying scopes",
    "rvn": "All non-magnifying scopes",
    "kobra": "All non-magnifying scopes",
    "m68": "All non-magnifying scopes",
    "red dot": "All non-magnifying scopes",
    "collimator": "All non-magnifying scopes",
    "large tents": "Large Tent",
    "medium tent": "Medium Tent",
    "canopy tent": "Canopy Tent",
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

# --- SMART PARSING LOGIC ---
def simple_pluralize(word):
    word = word.lower().strip()
    if word.endswith('s'): return word 
    if word.endswith('y'): return word[:-1] + "ies" 
    if word.endswith('x') or word.endswith('ch') or word.endswith('sh'): return word + "es"
    return word + "s"

@st.cache_data
def build_search_index(price_dict, aliases):
    index = {}
    for alias, real_name in aliases.items():
        clean_alias = alias.lower()
        index[clean_alias] = real_name
        index[simple_pluralize(clean_alias)] = real_name
    for real_name in price_dict.keys():
        clean_name = str(real_name).lower()
        index[clean_name] = real_name
        index[simple_pluralize(clean_name)] = real_name
        no_variant = re.sub(r'\(.*?\)', '', clean_name).strip()
        if no_variant:
            index[no_variant] = real_name
            index[simple_pluralize(no_variant)] = real_name
    return index

def clean_line_noise(line):
    line = line.replace(":", " ")
    line = re.sub(r'\s+and\s+', ',', line, flags=re.IGNORECASE)
    line = re.sub(r'&', ',', line)
    noise_words = ["box of", "boxes of", "box with", "pack of", "packs of", "can of", "cans of", " with "]
    for noise in noise_words:
        line = line.replace(noise, " ")
    return line

def extract_from_chunk(text, search_index):
    text_lower = text.lower()
    sorted_keys = sorted(search_index.keys(), key=len, reverse=True)
    found_item_key = None
    real_name_result = None
    
    for key in sorted_keys:
        start_idx = text_lower.find(key)
        if start_idx != -1:
            end_idx = start_idx + len(key)
            valid_start = True
            if start_idx > 0:
                char_before = text_lower[start_idx - 1]
                if char_before.isalpha() and char_before != 'x':
                    valid_start = False
            valid_end = True
            if end_idx < len(text_lower):
                char_after = text_lower[end_idx]
                if char_after.isalpha() and char_after != 'x':
                    valid_end = False
            if valid_start and valid_end:
                found_item_key = key
                real_name_result = search_index[key]
                break
            
    if found_item_key:
        text_without_item = text_lower.replace(found_item_key, " ", 1)
        qty_match = re.search(r'[xX]\s*(\d+)|(\d+)\s*[xX]|(\d+)', text_without_item)
        if qty_match:
            q_str = next((g for g in qty_match.groups() if g is not None), "1")
            quantity = int(q_str)
        else:
            quantity = 1
        return real_name_result, quantity, True
    else:
        qty_match = re.search(r'(\d+)', text)
        quantity = int(qty_match.group(1)) if qty_match else 1
        return text, quantity, False

def check_mode_switch(line):
    line_lower = line.lower()
    buy_keywords = ["want to buy", "buying", "wtb", "want to order", "ordering", "need", "buy", "grab"]
    for kw in buy_keywords:
        if kw in line_lower: return "COST", kw
    sell_keywords = ["want to sell", "selling", "wts", "i have", "have", "sell"]
    for kw in sell_keywords:
        if kw in line_lower: return "PAYOUT", kw
    return None, None

def is_ignored_line(line):
    ignore_starts = ["hello", "hi ", "dropping off", "code", "locker code", "blue locker"]
    line_clean = line.lower().strip()
    return any(line_clean.startswith(x) for x in ignore_starts)

# --- UPDATED PROCESSING LOGIC ---
def process_text_block(input_text, price_dict_buy, price_dict_sell, promo_info):
    combined_keys = {**price_dict_buy, **price_dict_sell} 
    search_index = build_search_index(combined_keys, ALIASES)

    raw_lines = input_text.split('\n')
    new_payout_items = []
    new_cost_items = []
    new_missing_items = []
    
    current_mode = "PAYOUT" # Default starts as selling
    
    for raw_line in raw_lines:
        if not raw_line.strip(): continue
        if is_ignored_line(raw_line): continue
        
        new_mode, keyword = check_mode_switch(raw_line)
        if new_mode:
            current_mode = new_mode
            line_content = re.sub(re.escape(keyword), "", raw_line, flags=re.IGNORECASE)
        else:
            line_content = raw_line

        line_content = clean_line_noise(line_content)
        comma_parts = line_content.split(',')
        
        for part in comma_parts:
            part = part.strip()
            if not part: continue
            
            item_name, qty, found = extract_from_chunk(part, search_index)
            price = 0
            
            if found:
                if item_name == "🔥🔥PROMO_ITEM🔥🔥":
                    if promo_info.get("active"):
                         price = promo_info.get("price")
                         item_name = f"🔥 {promo_info.get('name')}"
                elif promo_info.get("active") and promo_info.get("name").lower() in item_name.lower():
                     price = promo_info.get("price")
                     item_name = f"🔥 {promo_info.get('name')}"
                else:
                    # STRICT MODE LOOKUP: Use specific dict based on "buy/sell" keywords
                    if current_mode == "COST":
                        price = price_dict_sell.get(item_name, 0)
                    else:
                        price = price_dict_buy.get(item_name, 0)

            entry = {
                "Item": item_name, "Qty": qty, "Unit Price": price,
                "Total": qty * price, "Found": found, "Type": current_mode
            }

            if found and price > 0:
                if current_mode == "COST":
                    new_cost_items.append(entry)
                else:
                    new_payout_items.append(entry)
            else:
                new_missing_items.append(entry)
                
    return new_payout_items, new_cost_items, new_missing_items

def render_result_tables():
    resolved_payout = 0
    resolved_cost = 0

    if 'missing_df' in st.session_state and not st.session_state.missing_df.empty:
        st.warning("⚠️ **Items Not Found - Manual Resolution Needed:**")
        m_df = st.session_state.missing_df
        for index, row in m_df.iterrows():
            c1, c2, c3 = st.columns([3, 1, 3])
            with c1: st.write(f"❌ **{row['Item']}** (x{row['Qty']})")
            with c2: st.caption(f"Type: {row['Type']}")
            with c3:
                selected_cat = st.selectbox("Assign Category:", options=GENERIC_PRICES.keys(), key=f"cat_{index}_{row['Item']}", label_visibility="collapsed")
                price = GENERIC_PRICES[selected_cat]
                line_total = price * row['Qty']
                if line_total > 0:
                    if row['Type'] == "PAYOUT": resolved_payout += line_total
                    else: resolved_cost += line_total
                    st.success(f"+ ${line_total:,}")
        st.markdown("---")

    st.subheader("💰 Payout (We Buy)")
    payout_db_total = 0
    if 'buy_df' in st.session_state and not st.session_state.buy_df.empty:
        df = st.session_state.buy_df
        fmt_df = df.copy()
        fmt_df["Unit Price"] = fmt_df["Unit Price"].apply(lambda x: f"{x:,}")
        fmt_df["Total"] = fmt_df["Total"].apply(lambda x: f"{x:,}")
        st.table(fmt_df[["Item", "Qty", "Unit Price", "Total"]])
        payout_db_total = df['Total'].sum()
    
    final_payout = payout_db_total + resolved_payout
    st.success(f"### Total Payout: ${final_payout:,}")
    st.markdown("---")

    st.subheader("🛒 Cost (We Sell)")
    cost_db_total = 0
    if 'sell_df' in st.session_state and not st.session_state.sell_df.empty:
        df = st.session_state.sell_df
        fmt_df = df.copy()
        fmt_df["Unit Price"] = fmt_df["Unit Price"].apply(lambda x: f"{x:,}")
        fmt_df["Total"] = fmt_df["Total"].apply(lambda x: f"{x:,}")
        st.table(fmt_df[["Item", "Qty", "Unit Price", "Total"]])
        cost_db_total = df['Total'].sum()

    final_cost = cost_db_total + resolved_cost
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
    special_name = st.sidebar.text_input("Item Name", value=map_promo.get("name", ""))
    special_price_val = st.sidebar.text_input("Special Price", value=str(map_promo.get("price", 0)))
    try: special_price = int(special_price_val)
    except: special_price = 0
    
    if st.sidebar.button("🔄 Update Promo"):
        all_promos[selected_map] = {"active": special_item_active, "name": special_name, "price": special_price, "expiry": str(get_pst_today())}
        save_all_promos(all_promos)
        st.success("Promo Saved!")

    data = load_prices(selected_map)
    WE_BUY = data.get("WE_BUY", {})
    WE_SELL = data.get("TRADER_SELLS", {})

    if 'buy_df' not in st.session_state: st.session_state.buy_df = pd.DataFrame()
    if 'sell_df' not in st.session_state: st.session_state.sell_df = pd.DataFrame()
    if 'missing_df' not in st.session_state: st.session_state.missing_df = pd.DataFrame()

    st.markdown("### 📜 Smart Trade Processor")
    input_text = st.text_area("Paste Chat Log / Ticket:", height=200, key="master_input")
    
    if st.button("🚀 Process Ticket"):
        payouts, costs, missing = process_text_block(input_text, WE_BUY, WE_SELL, {"active": special_item_active, "name": special_name, "price": special_price})
        st.session_state.buy_df = pd.DataFrame(payouts) if payouts else pd.DataFrame()
        st.session_state.sell_df = pd.DataFrame(costs) if costs else pd.DataFrame()
        st.session_state.missing_df = pd.DataFrame(missing) if missing else pd.DataFrame()

    render_result_tables()
    st.button("🗑️ Clear All", on_click=clear_state)

if __name__ == "__main__":
    main()
