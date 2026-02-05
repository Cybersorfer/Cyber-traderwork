import streamlit as st
import re
import json
import pandas as pd
from thefuzz import process

# --- PAGE CONFIG ---
st.set_page_config(page_title="Cyber Trader Suite", page_icon="⚖️", layout="wide")

# --- SMART LOGIC FUNCTIONS ---
def load_prices():
    try:
        with open('prices.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"WE_BUY": {}, "WE_SELL": {}}

def smart_parse_line(line, price_dict):
    """
    Strips numbers, dashes, and spaces to find the item and quantity.
    Handles: '1-thermometer', 'thermometer 3', '2 - Santa hat', etc.
    """
    line = line.lower().strip()
    if not line:
        return None

    # 1. Extract quantity: Look for any digits (\d+)
    nums = re.findall(r'\d+', line)
    quantity = int(nums[0]) if nums else 1
    
    # 2. Clean item name: Remove digits and common separators like dashes
    item_clean = re.sub(r'\d+', '', line)
    item_clean = item_clean.replace('-', ' ').strip()
    
    if not item_clean:
        return None

    # 3. Fuzzy Match against the database keys
    choices = list(price_dict.keys())
    if not choices:
        return None
        
    match, score = process.extractOne(item_clean, choices)
    
    # 70 threshold to catch misspellings/partial names
    if score >= 70:
        price = price_dict[match]
        return {
            "Item": match, 
            "Qty": quantity, 
            "Unit Price": f"{price:,}", 
            "Total": quantity * price,
            "Raw_Total": quantity * price # Used for summing
        }
    return None

def render_tab(df_key, price_dict, type_label):
    st.subheader(f"📊 {type_label} Calculation")
    
    input_text = st.text_area(f"Paste {type_label} list here:", height=150, key=f"text_{df_key}")
    
    col1, col2 = st.columns([1, 4])
    
    if col1.button(f"🚀 Process {type_label}"):
        lines = input_text.split('\n')
        results = []
        for line in lines:
            parsed = smart_parse_line(line, price_dict)
            if parsed:
                results.append(parsed)
        
        if results:
            st.session_state[df_key] = pd.DataFrame(results)
        else:
            st.warning("No matches found. Check your item names or price list.")

    if not st.session_state[df_key].empty:
        # Display the table
        st.table(st.session_state[df_key][["Item", "Qty", "Unit Price", "Total"]])
        
        # Calculate and show Total
        total_sum = st.session_state[df_key]["Raw_Total"].sum()
        st.metric(label=f"Total {type_label} Value", value=f"{total_sum:,}")

# --- MAIN APP ---
def main():
    st.title("⚖️ Cyber Trader Economy Suite")
    
    data = load_prices()
    WE_BUY = data.get("WE_BUY", {})
    WE_SELL = data.get("WE_SELL", {})

    # Initialize session states for dataframes
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
