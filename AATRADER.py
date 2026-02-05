def smart_parse_line(line, price_dict):
    """
    Parses a single line of text to extract quantity and item name.
    Preserves numbers inside item names (e.g., 'M16', 'M4A1').
    """
    line = line.lower().strip()
    
    # 1. Basic garbage check
    if not line or len(line) < 2:
        return None

    # 2. SMART QUANTITY DETECTION
    quantity = 1
    item_clean = line

    # Check A: Number at the START (e.g., "5 m16" or "1 - m4a1")
    match_start = re.match(r'^(\d+)\s*[:-x\s]?\s*', line)
    
    # Check B: Number at the END (e.g., "m16 5" or "m4a1 - 1")
    match_end = re.search(r'\s*[:-x\s]?\s*(\d+)$', line)

    if match_start:
        quantity = int(match_start.group(1))
        # Remove only the found quantity from the start
        item_clean = line[match_start.end():] 
    elif match_end:
        quantity = int(match_end.group(1))
        # Remove only the found quantity from the end
        item_clean = line[:match_end.start()]

    # 3. Final cleanup (remove leftover dashes/spaces)
    item_clean = item_clean.replace('-', ' ').strip()
    
    # 4. PRIORITY CHECK: SPECIAL ITEM
    if special_item_active and not is_expired and special_name:
        if special_name.lower() in item_clean:
             return {
                "Item": f"🔥 {special_name} (SPECIAL)", 
                "Qty": quantity, 
                "Unit Price": special_price, 
                "Total": quantity * special_price
            }

    # 5. IGNORE RULE
    if "item of the week" in line:
        return None

    # 6. FUZZY MATCH (Standard Items)
    if not item_clean:
        return None

    choices = list(price_dict.keys())
    if not choices:
        return None
        
    match, score = process.extractOne(item_clean, choices)
    
    if score >= 80:
        price = price_dict[match]
        return {
            "Item": match, 
            "Qty": quantity, 
            "Unit Price": price, 
            "Total": quantity * price
        }
    return None
