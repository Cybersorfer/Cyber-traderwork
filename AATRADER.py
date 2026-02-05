import streamlit as st
import re
import json
import pandas as pd
from datetime import date
from thefuzz import process

# --- PAGE CONFIG ---
st.set_page_config(page_title="Cyber Trader Suite", page_icon="⚖️", layout="wide")

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
        return {"WE_BUY": {}, "WE_SELL": {}}

def smart_parse_line(line, price_dict):
    line = line.lower().strip()
    
    # 1. IGNORING RULE: Explicitly ignore the announcement line to prevent bugs
    if not line or len(line) < 2 or "item of the week" in line:
        return None

    # 2. Extract quantity
    nums = re.findall(r'\d+', line)
    quantity = int(nums[0]) if nums else 1
    
    # 3. Clean item name
    item_clean = re.sub(r'\d+', '', line)
    item_clean = item_clean.replace('-', ' ').strip()
    
    if not item_clean:
        return None

    # 4. CHECK SPECIAL ITEM OVERRIDE
    # If the user manually set a special item, check that first
    if special_item_active and not is_expired and special_name:
        # Simple text match for the special item
        if special_name.lower() in item_clean:
             return {
                "Item": f"🔥 {special_name} (SPECIAL)", 
                "Qty": quantity, 
                "Unit Price": special_price, 
                "Total": quantity * special_price
            }

    # 5. Fuzzy Match against database
    choices = list(price_dict.keys())
    if not choices:
        return None
        
    match, score = process.extractOne(item_clean, choices)
    
    # Threshold at 80 to be safe
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
        
        total_sum = df["Total"].sum()
        st.success(f"### Total {type_label} Value: {total_sum:,}")

# --- MAIN APP ---
def main():
    st.title("⚖️ Cyber Trader Economy Suite")
    
    if special_item_active and not is_expired and special_name:
        st.info(f"🔥 **ACTIVE PROMO:** {special_name} @ {special_price:,} until {expiry_date}")

    data = load_prices()
    WE_BUY = data.get("WE_BUY", {})
    WE_SELL = data.get("WE_SELL", {})

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
