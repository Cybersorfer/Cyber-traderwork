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
    except Exception:
        # Returns empty structure if file is missing or broken
        return {"WE_BUY": {}, "WE_SELL": {}}

def smart_parse_line(line, price_dict):
    """
    Handles messy inputs like '1-thermometer', 'thermometer 3', '2 - Santa hat'.
    """
    line = line.lower().strip()
    if not line or len(line) < 2:
        return None

    # 1. Extract quantity (finds digits anywhere in the line)
    nums = re.findall(r'\d+', line)
    quantity = int(nums[0]) if nums else 1
    
    # 2. Clean item name (remove digits and dashes)
    item_clean = re.sub(r'\d+', '', line)
    item_clean = item_clean.replace('-', ' ').strip()
    
    if not item_clean:
        return None

    # 3. Fuzzy Match against the database
    choices = list(price_dict.keys())
    if not choices:
        return None
        
    match, score = process.extractOne(item_clean, choices)
    
    # Threshold set to 70 to catch typos while staying accurate
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
            st.warning("No matches found. Ensure items are in your prices.json.")

    # SAFETY CHECK: Only display the table if the dataframe has the required columns
    df = st.session_state[df_key]
    if not df.empty and "Item" in df.columns:
        # Display the table with nice formatting
        formatted_df = df.copy()
        formatted_df["Unit Price"] = formatted_df["Unit Price"].apply(lambda x: f"{x:,}")
        formatted_df["Total"] = formatted_df["Total"].apply(lambda x: f"{x:,}")
        
        st.table(formatted_df[["Item", "Qty", "Unit Price", "Total"]])
        
        # Calculate Total Sum
        total_sum = df["Total"].sum()
        st.success(f"### Total {type_label} Value: {total_sum:,}")

# --- MAIN APP ---
def main():
    st.title("⚖️ Cyber Trader Economy Suite")
    
    data = load_prices()
    # Support both "WE_BUY" and "WE_SELL" formats
    WE_BUY = data.get("WE_BUY", {})
    WE_SELL = data.get("WE_SELL", {})

    # Initialize dataframes in session state if they don't exist
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

