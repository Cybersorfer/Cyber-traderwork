import streamlit as st
import re
import json
import os
import pandas as pd
import pytz 
from datetime import datetime, date

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

# --- ALIAS LIST ---
ALIASES = {
    # --- PROMOS ---
    "item of the week": "🔥🔥PROMO_ITEM🔥🔥",
    "item of week": "🔥🔥PROMO_ITEM🔥🔥",
    "promo item": "🔥🔥PROMO_ITEM🔥🔥",

    # --- CLOTHING: Anniversary & Holiday ---
    "anniversary tshirt": "10th Anniversary Tshirt",
    "anniversary t-shirt": "10th Anniversary Tshirt",
    "30th anniversary tshirt": "10th Anniversary Tshirt",
    "santa hats": "Santa Hat",
    "santa beard": "Santa Beard",

    # --- CLOTHING: General --- 
    "other tops": "All other tops",
    "tops": "All other tops",
    "shirt": "All other tops",
    "tshirt": "All other tops",
    "t-shirt": "All other tops",
    "jacket": "All other tops",
    "sweater": "All other tops",
    "upper body": "All other tops",
    "hat": "All Other Hats and masks",
    "mask": "All Other Hats and masks",
    "googles": "All Other Hats and masks",
    "goggles": "All Other Hats and masks",
    "glasses": "All Other Hats and masks",
    "sunglasses": "All Other Hats and masks",
    "pants": "All other pants",
    "Shorts": "All other pants",
    "bottoms": "All other pants",
    "lower body": "All other pants",
    "Yellow Scarred Helmet": "Yellow Scarred Moto Helmet",
    "Scarred moto Helmet": "Yellow Scarred Moto Helmet",
    "Scarred Helmet": "Yellow Scarred Moto Helmet",
    "King helmet": "Yellow Scarred Moto Helmet",
    "NVGs": "Night Vision Goggles",
    "NVG": "Night Vision Goggles",

    # --- WEAPONS: Melee ---
    "knife": "All Melee Weapons",
    "machete": "All Melee Weapons",
    "mace": "All Melee Weapons",
    "bat": "All Melee Weapons",
    "fange": "All Melee Weapons",
    "sword": "All Melee Weapons",

    # --- WEAPONS: Guns ---
    "pistol": "All other unlisted guns",
    "rifle": "All other unlisted guns",
    "M79": "M79 Grenade Launcher",
    "Savanna": "CR-550 Savanna",
    "SavannaH": "CR-550 Savanna",
    "CR-550 Savannah": "CR-550 Savanna",
    "savannah": "CR-550 Savanna",
    "vihker": "Vikhr",
    "vihkr": "Vikhr",
    "KA-101": "KA101",
    "lar": "LAR",
    "m16": "M16-A2",
    "m4": "M4-A1",
    "ak": "KA-74",
	"ak74": "KA-74",
	"ka74": "KA-74",
    "vs": "VSS",
    "vs89": "VS-89",
    "vsd": "VSD",
	"vds": "VSD",
    "val": "SVAL",

    # --- AMMO: Calibers ---
    ".22": ".22 LR Ammo Box",
	".22 ammo": ".22 LR Ammo Box",
	".22 box": ".22 LR Ammo Box",
    ".22lr": ".22 LR Ammo Box",
    "5.56": "5.56x45 Ammo Box",
	"5.56mm": "5.56x45 Ammo Box",
    "5,56": "5.56x45 Ammo Box",
    "5,56x45": "5.56x45 Ammo Box",
    "5.56x45mm": "5.56x45 Ammo Box",
    "5.56x45 mm": "5.56x45 Ammo Box",
    "5.45": "5.45x39 Ammo Box",
	"5.45ammo": "5.45x39 Ammo Box",
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
	"win ammo": ".308 WIN Ammo Box",
    "308": ".308 WIN Ammo Box",
    ".308": ".308 WIN Ammo Box",
    "357": ".357 Ammo Box",
    ".357": ".357 Ammo Box",
    "12g": "12ga Ammo Box",
    "12ga": "12ga Ammo Box",
    "9x39": "9x39 Ammo Box",
    "9x39mm": "9x39 Ammo Box",
    "9x39 mm": "9x39 Ammo Box",
    ".45 ACP": ".45 ACP Ammo Box",
    ".45ACP": ".45 ACP Ammo Box",
    ".45": ".45 ACP Ammo Box",

    # --- AMMO: Categories ---
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
    "rifle ammo": "higher Ammo Box",
    "rifle ammo box": "higher Ammo Box",
    "high caliber ammo": "higher Ammo Box",
    "high caliber": "higher Ammo Box",
    "higher caliber ammo": "higher Ammo Box",
    "high ammo": "higher Ammo Box",

    # --- SCOPES ---
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

    # --- CONSUMABLES: Medical & Food ---
    "POX": "POX Antidote",
    "Antidote": "POX Antidote",
    "Medical Pouch": "First Aid Pouch",
    "Aid Pouch": "First Aid Pouch",
    "zagorty": "Zagorky",
    "zagorky snacks": "Zagorky",
    "snacks": "Zagorky",
    "unknown food": "Unknown Food Can",
    "unknown can": "Unknown Food Can",

    # --- CONSUMABLES: Smokes ---
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

    # --- DRUGS / WEED ---
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
    "Cannabis Seeds": "Cannabis Seed Pack",
    "Weed Seeds": "Cannabis Seed Pack",
    "weed Seed Pack": "Cannabis Seed Pack",
    "weed seeds": "Cannabis Seed Pack",
    "cannabis seed": "Cannabis Seed Pack",
	"dried buds": "Weed (per bud)",
	"dried budz": "Weed (per bud)",

    # --- TOOLS & MATERIALS ---
    "prn": "Pen",
    "ptn": "Pen",
	"pencil": "Pen",
}

# --- HELPERS ---
def get_pst_now():
    pst = pytz.timezone('US/Pacific')
    return datetime.now(pst)

def simple_pluralize(word):
    word = word.lower().strip()
    if word.endswith('s'): return word 
    if word.endswith('y'): return word[:-1] + "ies" 
    if word.endswith('x') or word.endswith('ch') or word.endswith('sh'): return word + "es"
    return word + "s"

def get_price_case_insensitive(item_name, price_dict):
    """Checks the dictionary for a key matching item_name regardless of case."""
    target = item_name.lower()
    for k, v in price_dict.items():
        if k.lower() == target:
            return v
    return 0

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
        quantity = int(next((g for g in qty_match.groups() if g is not None), "1")) if qty_match else 1
        return real_name_result, quantity, True
    else:
        qty_match = re.search(r'(\d+)', text)
        return text, int(qty_match.group(1)) if qty_match else 1, False

def check_mode_switch(line):
    line_lower = line.lower()
    if any(kw in line_lower for kw in ["buying", "wtb", "buy", "order"]): return "COST", "buy"
    if any(kw in line_lower for kw in ["selling", "wts", "have", "sell"]): return "PAYOUT", "sell"
    return None, None

def load_prices(map_name):
    file_path = MAPS.get(map_name, "prices_chernarus.json")
    try:
        with open(file_path, 'r') as f: return json.load(f)
    except: return {"WE_BUY": {}, "TRADER_SELLS": {}}

def load_all_promos():
    if os.path.exists(PROMO_FILE):
        try:
            with open(PROMO_FILE, 'r') as f: return json.load(f)
        except: pass
    return {}

def save_all_promos(data):
    with open(PROMO_FILE, 'w') as f: json.dump(data, f)

def clean_line_noise(line):
    line = line.replace(":", " ")
    noise_words = ["box of", "boxes of", "pack of", "can of", " with "]
    for noise in noise_words: line = line.replace(noise, " ")
    return line

def clear_state():
    st.session_state.buy_df = pd.DataFrame()
    st.session_state.sell_df = pd.DataFrame()
    st.session_state.missing_df = pd.DataFrame()
    st.session_state.master_input = ""

# --- PROCESSING ---
def process_text_block(input_text, price_dict_buy, price_dict_sell, promo_info):
    search_index = build_search_index({**price_dict_buy, **price_dict_sell}, ALIASES)
    payouts, costs, missing = [], [], []
    current_mode = "PAYOUT"
    
    for line in input_text.split('\n'):
        if not line.strip(): continue
        new_mode, kw = check_mode_switch(line)
        if new_mode:
            current_mode = new_mode
            line = re.sub(re.escape(kw), "", line, flags=re.IGNORECASE)

        line = clean_line_noise(line)
        
        # Split by comma
        for part in line.split(','):
            part = part.strip()
            # FIX: Skip empty parts (prevents ghost rows)
            if not part: continue
            
            item_name, qty, found = extract_from_chunk(part, search_index)
            price = 0
            
            # Additional safety: If item name ended up empty
            if not str(item_name).strip(): continue

            if found:
                if item_name == "🔥🔥PROMO_ITEM🔥🔥" or (promo_info.get('active') and promo_info.get('name', '').lower() in item_name.lower()):
                    price = promo_info.get('price', 0)
                    item_name = f"🔥 {promo_info.get('name', item_name)}"
                else:
                    # Strict Mode Lookup
                    target_dict = price_dict_sell if current_mode == "COST" else price_dict_buy
                    price = get_price_case_insensitive(item_name, target_dict)

            entry = {"Item": item_name, "Qty": qty, "Unit Price": price, "Total": qty * price, "Type": current_mode}
            if found and price > 0:
                (costs if current_mode == "COST" else payouts).append(entry)
            else: missing.append(entry)
    return payouts, costs, missing

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
        div[data-baseweb="input"] { background-color: #1E1E1E !important; border-color: #4CAF50 !important; }
        div[data-baseweb="select"] > div { background-color: #1E1E1E !important; color: #00FF00 !important; border-color: #4CAF50 !important; }
        .stButton>button { color: #FAFAFA; background-color: #262730; border: 1px solid #4CAF50; transition: all 0.3s ease; }
        .stButton>button:hover { background-color: #4CAF50; color: #000000; box-shadow: 0 0 10px #4CAF50; }
        table { color: #E0E0E0 !important; background-color: transparent !important; border-collapse: collapse; width: 100%; }
        thead tr th { background-color: #262730 !important; color: #00FF00 !important; border-bottom: 2px solid #4CAF50 !important; }
        tbody tr { border-bottom: 1px solid #333 !important; }
        tbody tr:hover { background-color: #1E1E1E !important; }
        td { color: #E0E0E0 !important; }
        [data-testid="stMetricValue"], [data-testid="stMetricLabel"] { color: #4CAF50 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- UI ---
def main():
    set_theme()
    st.sidebar.title("🌍 Map Selector")
    selected_map = st.sidebar.selectbox("Select Server Map:", list(MAPS.keys()))
    
    # Load Promo Data
    all_promos = {m: {"active": False, "name": "", "price": 0} for m in MAPS}
    if os.path.exists(PROMO_FILE):
        try: 
            with open(PROMO_FILE, 'r') as f: all_promos.update(json.load(f))
        except: pass
    
    map_promo = all_promos.get(selected_map, {"active": False, "name": "", "price": 0})
    st.sidebar.header(f"🔥 {selected_map} Promo")
    p_active = st.sidebar.checkbox("Enable Special Price", value=map_promo['active'])
    p_name = st.sidebar.text_input("Item Name", value=map_promo['name'])
    p_price = st.sidebar.number_input("Special Price", value=int(map_promo['price']))
    
    if st.sidebar.button("🔄 Update Promo"):
        all_promos[selected_map] = {"active": p_active, "name": p_name, "price": p_price}
        with open(PROMO_FILE, 'w') as f: json.dump(all_promos, f)
        st.rerun()

    # Load Prices
    try:
        with open(MAPS[selected_map], 'r') as f: data = json.load(f)
    except: data = {"WE_BUY": {}, "TRADER_SELLS": {}}
    WE_BUY, WE_SELL = data.get("WE_BUY", {}), data.get("TRADER_SELLS", {})

    st.title(f"⚖️ {selected_map} Economy Suite")
    input_text = st.text_area("Paste Ticket Here:", height=200, key="master_input")
    
    if 'buy_df' not in st.session_state: st.session_state.buy_df = pd.DataFrame()
    if 'sell_df' not in st.session_state: st.session_state.sell_df = pd.DataFrame()
    if 'missing_df' not in st.session_state: st.session_state.missing_df = pd.DataFrame()

    if st.button("🚀 Process Ticket"):
        p, c, m = process_text_block(input_text, WE_BUY, WE_SELL, all_promos[selected_map])
        st.session_state.buy_df, st.session_state.sell_df, st.session_state.missing_df = pd.DataFrame(p), pd.DataFrame(c), pd.DataFrame(m)

    # --- CALCULATE MANUAL RESOLUTIONS ---
    resolved_payout = 0
    resolved_cost = 0

    # Display Missing Items with Manual Category Selector
    if not st.session_state.missing_df.empty:
        st.warning("⚠️ **Items Not Found - Manual Resolution Needed:**")
        
        m_df = st.session_state.missing_df
        # Double check to filter out empty rows just in case
        m_df = m_df[m_df["Item"].str.strip().astype(bool)]
        
        for index, row in m_df.iterrows():
            c1, c2, c3 = st.columns([3, 1, 3])
            with c1:
                st.write(f"❌ **{row['Item']}** (x{row['Qty']})")
            with c2:
                st.caption(f"Type: {row['Type']}")
            with c3:
                cat_key = f"cat_{index}_{row['Item']}"
                selected_cat = st.selectbox(
                    "Assign Category:", 
                    options=GENERIC_PRICES.keys(), 
                    key=cat_key,
                    label_visibility="collapsed"
                )
                
                price = GENERIC_PRICES[selected_cat]
                line_total = price * row['Qty']
                
                if line_total > 0:
                    if row['Type'] == "PAYOUT":
                        resolved_payout += line_total
                    else:
                        resolved_cost += line_total
                    st.success(f"+ ${line_total:,}")
        st.markdown("---")

    # Tables
    if not st.session_state.buy_df.empty:
        st.subheader("💰 Payout (We Buy)")
        df = st.session_state.buy_df.copy()
        df["Unit Price"] = df["Unit Price"].apply(lambda x: f"{x:,}")
        df["Total"] = df["Total"].apply(lambda x: f"{x:,}")
        st.table(df)
        
        final_payout = st.session_state.buy_df['Total'].sum() + resolved_payout
        if resolved_payout > 0:
            st.success(f"### Total: ${st.session_state.buy_df['Total'].sum():,} (DB) + ${resolved_payout:,} (Resolved) = ${final_payout:,}")
        else:
            st.success(f"### Total Payout: ${final_payout:,}")

    if not st.session_state.sell_df.empty:
        st.subheader("🛒 Cost (We Sell)")
        df = st.session_state.sell_df.copy()
        df["Unit Price"] = df["Unit Price"].apply(lambda x: f"{x:,}")
        df["Total"] = df["Total"].apply(lambda x: f"{x:,}")
        st.table(df)
        
        final_cost = st.session_state.sell_df['Total'].sum() + resolved_cost
        if resolved_cost > 0:
            st.error(f"### Total: ${st.session_state.sell_df['Total'].sum():,} (DB) + ${resolved_cost:,} (Resolved) = ${final_cost:,}")
        else:
            st.error(f"### Total Due: ${final_cost:,}")

    # --- CLEAN PRICE SEARCH ---
    with st.expander("🕵️ Search Price Database"):
        q = st.text_input("Search Item Name").lower()
        if q:
            hits_buy = {k: v for k, v in WE_BUY.items() if q in str(k).lower()}
            hits_sell = {k: v for k, v in WE_SELL.items() if q in str(k).lower()}
            
            if hits_buy:
                st.markdown("### 💰 WE BUY:")
                for name, price in hits_buy.items():
                    st.write(f"**{name}**: ${price:,}")
                    
            if hits_sell:
                st.markdown("### 🛒 TRADER SELLS:")
                for name, price in hits_sell.items():
                    st.write(f"**{name}**: ${price:,}")

            if not hits_buy and not hits_sell:
                st.warning("No items found matching your search.")

    st.button("🗑️ Clear All", on_click=clear_state)

if __name__ == "__main__":
    main()
