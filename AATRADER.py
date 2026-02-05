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
    
    # Threshold set to 80 to avoid false positives (e.g. "Stove" matching "Smokes")
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

    # Display Table Logic (Safety Check included)
    df = st.session_state[df_key]
    if not df.empty and "Item" in df.columns:
        # Create a copy for formatting to avoid modifying the math data
        formatted_df = df.copy()
        formatted_df["Unit Price"] = formatted_df["Unit Price"].apply(lambda x: f"{x:,}")
        formatted_df["Total"] = formatted_df["Total"].apply(lambda x: f"{x:,}")
        
        st.table(formatted_df[["Item", "Qty", "Unit Price", "Total"]])
        
        # Calculate Sum from original numeric data
        total_sum = df["Total"].sum()
        st.success(f"### Total {type_label} Value: {total_sum:,}")

# --- MAIN APP ---
def main():
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
