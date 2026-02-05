import streamlit as st
import re
import json
from thefuzz import process, fuzz
from PIL import Image
import pytesseract
import pandas as pd
import os

# --- OCR ENGINE PATH (LOCKED) ---
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def load_prices():
    if os.path.exists('prices.json'):
        with open('prices.json', 'r') as f:
            return json.load(f)
    return {"WE_BUY": {}, "TRADER_SELLS": {}}

data = load_prices()
WE_BUY = {"--- SELECT ITEM ---": 0.0, **data['WE_BUY']}
TRADER_SELLS = {"--- SELECT ITEM ---": 0.0, **data['TRADER_SELLS']}

def run_smart_calc(input_text, price_dict):
    breakdown = []
    # Normalize text and split into words to find items hidden in sentences
    words_in_text = re.findall(r'\w+', input_text.lower())
    
    # Expand "Slash Categories" into searchable individuals (e.g., Shovel/Pickaxe)
    search_map = {}
    for official_name, price in price_dict.items():
        if "/" in official_name:
            for part in official_name.split("/"):
                search_map[part.strip().lower()] = (official_name, price)
        else:
            search_map[official_name.lower()] = (official_name, price)

    # Keyword Hunting Logic
    found_items = []
    for i, word in enumerate(words_in_text):
        if len(word) < 3: continue
        
        # Match word against the expanded database
        match, score = process.extractOne(word, search_map.keys(), scorer=fuzz.ratio)
        
        if score >= 85 and match != "--- select item ---":
            official_name, price = search_map[match]
            
            # Smart Quantity Detection: Check the word immediately before the item
            qty = 1
            if i > 0 and words_in_text[i-1].isdigit():
                qty = int(words_in_text[i-1])
            
            if official_name not in found_items:
                breakdown.append({
                    "Item Name": official_name, 
                    "Quantity": qty, 
                    "Price ($)": float(price)
                })
                found_items.append(official_name)
                
    return pd.DataFrame(breakdown)

# --- UI SETUP ---
st.set_page_config(page_title="Cyber Trader Calc", page_icon="🏹", layout="wide")
st.title("🏹 Cyber Trader Economy Suite")

if "ocr_text" not in st.session_state: st.session_state.ocr_text = ""
if "buy_df" not in st.session_state: st.session_state.buy_df = pd.DataFrame(columns=["Item Name", "Quantity", "Price ($)"])
if "sell_df" not in st.session_state: st.session_state.sell_df = pd.DataFrame(columns=["Item Name", "Quantity", "Price ($)"])

with st.sidebar:
    st.header("📸 Ticket Scanner")
    uploaded_file = st.file_uploader("Upload Ticket Screenshot", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file:
        img = Image.open(uploaded_file)
        # PSM 6 is best for uniform blocks of text like chat messages
        text = pytesseract.image_to_string(img, config='--psm 6')
        
        if text != st.session_state.ocr_text:
            st.session_state.ocr_text = text
            # Immediately push results into the tables
            st.session_state.buy_df = run_smart_calc(text, WE_BUY)
            st.session_state.sell_df = run_smart_calc(text, TRADER_SELLS)
            st.success("✅ Scan & Chat Detection Complete!")

tab1, tab2 = st.tabs(["💰 WE BUY (Payout)", "🛒 WE SELL (Cost)"])

def render_tab(df, price_dict, key_prefix, txt_val):
    txt_input = st.text_area("Scanned Text / Manual Input", value=txt_val, height=150, key=f"txt_{key_prefix}")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🚀 Process Text", key=f"run_{key_prefix}"):
            df = run_smart_calc(txt_input, price_dict)
    with c2:
        if st.button("➕ Add Item", key=f"add_{key_prefix}"):
            new_row = pd.DataFrame([{"Item Name": "--- SELECT ITEM ---", "Quantity": 1, "Price ($)": 0.0}])
            df = pd.concat([df, new_row], ignore_index=True)
    with c3:
        if st.button("🔄 Update Totals", key=f"upd_{key_prefix}"):
            st.rerun()

    # Automatic Price Sync for manual edits
    if not df.empty and "Item Name" in df.columns:
        df["Price ($)"] = df["Item Name"].map(price_dict).fillna(0).astype(float)
        
    edited_df = st.data_editor(
        df, use_container_width=True, num_rows="dynamic",
        column_config={
            "Item Name": st.column_config.SelectboxColumn("Item Name", options=list(price_dict.keys()), required=True),
            "Price ($)": st.column_config.NumberColumn(disabled=True)
        },
        key=f"edit_{key_prefix}"
    )
    
    if not edited_df.empty:
        total = (edited_df["Quantity"] * edited_df["Price ($)"]).sum()
        st.success(f"### Total: ${total:,.0f}")
        return edited_df
    return df

with tab1:
    st.session_state.buy_df = render_tab(st.session_state.buy_df, WE_BUY, "buy", st.session_state.ocr_text)

with tab2:
    st.session_state.sell_df = render_tab(st.session_state.sell_df, TRADER_SELLS, "sell", st.session_state.ocr_text)

if st.button("🗑️ Clear All"):
    st.session_state.ocr_text = ""
    st.session_state.buy_df = pd.DataFrame(columns=["Item Name", "Quantity", "Price ($)"])
    st.session_state.sell_df = pd.DataFrame(columns=["Item Name", "Quantity", "Price ($)"])
    st.rerun()