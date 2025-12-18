import streamlit as st
import pandas as pd
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Delta Violation Penalty Calculator",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f2937;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    .info-box {
        background-color: #eff6ff;
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1.5rem;
    }
    .warning-box {
        background-color: #fef3c7;
        border-left: 4px solid #f59e0b;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-top: 1.5rem;
    }
    .violation-box {
        background-color: #fee2e2;
        border: 2px solid #ef4444;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-top: 1rem;
    }
    .safe-box {
        background-color: #d1fae5;
        border: 2px solid #10b981;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-top: 1rem;
    }
    .old-position-box {
        background-color: #f3f4f6;
        border: 2px solid #6b7280;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .new-position-box {
        background-color: #dbeafe;
        border: 2px solid #3b82f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .stock-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'old_positions' not in st.session_state:
    st.session_state.old_positions = []
if 'new_positions' not in st.session_state:
    st.session_state.new_positions = []
if 'stock_name' not in st.session_state:
    st.session_state.stock_name = ""

def calculate_position_delta(pos_type, direction, qty, delta_value):
    """Calculate the delta for a single position
    Formula: Delta × Quantity
    """
    qty = float(qty)
    delta_value = float(delta_value)
    
    if pos_type == "Future":
        effective_delta = 1 if direction == "Long" else -1
        return effective_delta * qty
    elif pos_type == "Call Option":
        effective_delta = delta_value if direction == "Long" else -delta_value
        return effective_delta * qty
    else:  # Put Option
        if direction == "Long":
            effective_delta = -abs(delta_value)
        else:
            effective_delta = abs(delta_value)
        return effective_delta * qty

def calculate_penalty(delta_violation, stock_price):
    """Calculate the penalty amount"""
    penalty_amount = abs(delta_violation) * stock_price * 0.01
    final_penalty = max(5000, min(100000, penalty_amount))
    gst = final_penalty * 0.18
    total_penalty = final_penalty + gst
    return penalty_amount, final_penalty, gst, total_penalty

def check_violation(net_delta, base_delta):
    """Check if there's a delta violation
    Returns: (has_violation, violation_quantity, violation_reason)
    """
    if base_delta == 0:
        return (net_delta != 0, abs(net_delta), "From zero to non-zero")
    
    # Check if sign changed
    sign_changed = (net_delta > 0 and base_delta < 0) or (net_delta < 0 and base_delta > 0)
    
    if sign_changed:
        # When sign changes, violation quantity is the absolute value of (net_delta - base_delta)
        violation_qty = abs(net_delta - base_delta)
        return (True, violation_qty, f"Sign changed from {'negative to positive' if net_delta > 0 else 'positive to negative'}")
    
    # Same sign - check if delta increased
    if base_delta < 0:
        # For negative deltas, moving towards zero or positive is an increase
        delta_increased = net_delta > base_delta
    else:
        # For positive deltas, becoming more positive is an increase
        delta_increased = net_delta > base_delta
    
    if delta_increased:
        violation_qty = abs(net_delta - base_delta)
        return (True, violation_qty, "Net Delta increased in same direction")
    
    return (False, 0, "No violation - Delta decreased or remained same")

# Header
st.markdown('<div class="main-header">📊 Delta Violation Penalty Calculator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Calculate penalties for F&O positions during ban period</div>', unsafe_allow_html=True)

# Securities under ban period banner
st.markdown("""
    <div style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); 
                color: white; 
                padding: 1rem 1.5rem; 
                border-radius: 0.5rem; 
                margin-bottom: 1.5rem;
                border-left: 5px solid #991b1b;
                box-shadow: 0 4px 6px rgba(239, 68, 68, 0.3);">
        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;">
            <span style="font-size: 1.5rem;">🚨</span>
            <h3 style="margin: 0; font-size: 1.2rem; font-weight: bold;">Securities Under Ban Period</h3>
        </div>
        <p style="margin: 0; opacity: 0.95; font-size: 0.95rem;">
            <strong>As of 16 Dec 2025:</strong> BANDHANBNK
        </p>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.85; font-size: 0.85rem;">
            ⚠️ No fresh positions allowed. Only square-off or reducing positions permitted.
        </p>
    </div>
""", unsafe_allow_html=True)

# Stock Name Input Section
st.markdown("### 🏢 Stock/Contract Details")
col_stock1, col_stock2 = st.columns([2, 1])

with col_stock1:
    stock_name = st.text_input(
        "Stock/Contract Name",
        value=st.session_state.stock_name,
        placeholder="e.g., BANDHANBNK, SAMMAANCAP, KAYNES",
        help="Enter the stock or contract name in ban period"
    )
    st.session_state.stock_name = stock_name

with col_stock2:
    stock_price = st.number_input(
        "Underlying Price (₹)",
        min_value=0.0,
        value=135.47,
        step=0.01,
        help="Closing price on the day delta was violated"
    )

# Display stock info banner
if stock_name:
    st.markdown(f"""
    <div class="stock-header">
        <h2 style="margin: 0;">📈 {stock_name}</h2>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Underlying Price: ₹{stock_price:,.2f}</p>
    </div>
    """, unsafe_allow_html=True)

# Info section
with st.expander("ℹ️ Understanding Delta and Violations", expanded=False):
    st.markdown("""
    ### What is Delta?
    Delta tells you how much an option's premium will move when the stock moves by ₹1.
    
    ### Delta Values
    - **Futures**: Long = +1, Short = -1 (per quantity)
    - **Long Call**: 0 to +1 | **Short Call**: -1 to 0
    - **Long Put**: -1 to 0 | **Short Put**: 0 to +1
    
    ### When Does Violation Occur?
    1. **Net Delta exceeds Base Delta** (increases in same sign direction)
    2. **Sign changes** (+ve to -ve or vice versa)
    
    ### Penalty Formula
    ```
    Violation Quantity = |Net Delta - Base Delta|
    Penalty = Violation Quantity × Underlying Price × 1%
    Min: ₹5,000 + GST (18%) | Max: ₹1,00,000 + GST per day
    ```
    """)

# Main layout - Two column design
col_left, col_right = st.columns([1, 1])

# LEFT COLUMN - OLD POSITIONS (BASE)
with col_left:
    st.markdown('<div class="old-position-box">', unsafe_allow_html=True)
    st.markdown("### 📅 OLD POSITIONS (EOD When Ban Started)")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Form to add old positions
    with st.form("add_old_position_form", clear_on_submit=True):
        st.write("**Add Position**")
        old_cols = st.columns([2, 2, 2, 2, 1])
        
        with old_cols[0]:
            old_type = st.selectbox("Type", ["Call Option", "Put Option", "Future"], key="old_type")
        
        with old_cols[1]:
            old_direction = st.selectbox("Direction", ["Long", "Short"], key="old_direction")
        
        with old_cols[2]:
            old_qty = st.number_input("Quantity", min_value=1, value=7200, step=1, key="old_qty")
        
        with old_cols[3]:
            old_delta = st.text_input("Delta", value="0.02323", key="old_delta")
        
        with old_cols[4]:
            old_add = st.form_submit_button("➕", use_container_width=True)
        
        if old_add:
            try:
                delta_val = float(old_delta)
                position_delta = calculate_position_delta(old_type, old_direction, old_qty, delta_val)
                st.session_state.old_positions.append({
                    'Type': old_type,
                    'Direction': old_direction,
                    'Quantity': old_qty,
                    'Delta': old_delta,
                    'Position Delta': position_delta
                })
                st.success(f"✅ Added! Delta: {position_delta}")
                st.rerun()
            except ValueError:
                st.error("Invalid delta value")
    
    # Display old positions
    if st.session_state.old_positions:
        df_old = pd.DataFrame(st.session_state.old_positions)
        st.dataframe(df_old, use_container_width=True, hide_index=True)
        
        old_net_delta = sum([pos['Position Delta'] for pos in st.session_state.old_positions])
        st.info(f"**Old Net Delta (Base Delta): {old_net_delta:.4f}**")
        
        col_old1, col_old2 = st.columns(2)
        with col_old1:
            if st.button("↩️ Remove Last (Old)", key="remove_old", use_container_width=True):
                st.session_state.old_positions.pop()
                st.rerun()
        with col_old2:
            if st.button("🗑️ Clear All (Old)", key="clear_old", use_container_width=True):
                st.session_state.old_positions = []
                st.rerun()
    else:
        st.info("Add old positions (EOD when contract entered ban period)")

# RIGHT COLUMN - NEW POSITIONS (AFTER TRADE)
with col_right:
    st.markdown('<div class="new-position-box">', unsafe_allow_html=True)
    st.markdown("### 🔄 NEW POSITIONS (After Trade/Modification)")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Form to add new positions
    with st.form("add_new_position_form", clear_on_submit=True):
        st.write("**Add Position**")
        new_cols = st.columns([2, 2, 2, 2, 1])
        
        with new_cols[0]:
            new_type = st.selectbox("Type", ["Call Option", "Put Option", "Future"], key="new_type")
        
        with new_cols[1]:
            new_direction = st.selectbox("Direction", ["Long", "Short"], key="new_direction")
        
        with new_cols[2]:
            new_qty = st.number_input("Quantity", min_value=0, value=3600, step=1, key="new_qty")
        
        with new_cols[3]:
            new_delta = st.text_input("Delta", value="0.00562", key="new_delta")
        
        with new_cols[4]:
            new_add = st.form_submit_button("➕", use_container_width=True)
        
        if new_add:
            try:
                delta_val = float(new_delta)
                position_delta = calculate_position_delta(new_type, new_direction, new_qty, delta_val)
                st.session_state.new_positions.append({
                    'Type': new_type,
                    'Direction': new_direction,
                    'Quantity': new_qty,
                    'Delta': new_delta,
                    'Position Delta': position_delta
                })
                st.success(f"✅ Added! Delta: {position_delta}")
                st.rerun()
            except ValueError:
                st.error("Invalid delta value")
    
    # Display new positions
    if st.session_state.new_positions:
        df_new = pd.DataFrame(st.session_state.new_positions)
        st.dataframe(df_new, use_container_width=True, hide_index=True)
        
        new_net_delta = sum([pos['Position Delta'] for pos in st.session_state.new_positions])
        st.success(f"**New Net Delta: {new_net_delta:.4f}**")
        
        col_new1, col_new2 = st.columns(2)
        with col_new1:
            if st.button("↩️ Remove Last (New)", key="remove_new", use_container_width=True):
                st.session_state.new_positions.pop()
                st.rerun()
        with col_new2:
            if st.button("🗑️ Clear All (New)", key="clear_new", use_container_width=True):
                st.session_state.new_positions = []
                st.rerun()
    else:
        st.info("Add new positions (after trade/modification)")

# Quick Copy Button
st.markdown("---")
col_copy1, col_copy2, col_copy3 = st.columns([1, 1, 2])
with col_copy1:
    if st.button("📋 Copy Old → New", use_container_width=True):
        if st.session_state.old_positions:
            st.session_state.new_positions = [pos.copy() for pos in st.session_state.old_positions]
            st.success("✅ Copied old positions to new!")
            st.rerun()
        else:
            st.warning("No old positions to copy")

with col_copy2:
    if st.button("🔄 Clear Both", use_container_width=True):
        st.session_state.old_positions = []
        st.session_state.new_positions = []
        st.rerun()

# RESULTS SECTION
st.markdown("---")
st.markdown("## 📊 RESULTS & PENALTY CALCULATION")

if st.session_state.old_positions or st.session_state.new_positions:
    # Calculate deltas
    base_delta = sum([pos['Position Delta'] for pos in st.session_state.old_positions])
    net_delta = sum([pos['Position Delta'] for pos in st.session_state.new_positions])
    
    # Display metrics
    col_res1, col_res2, col_res3 = st.columns(3)
    
    with col_res1:
        st.metric("Base Delta (Old)", f"{base_delta:.4f}")
    
    with col_res2:
        st.metric("Net Delta (New)", f"{net_delta:.4f}")
    
    with col_res3:
        delta_change = net_delta - base_delta
        st.metric("Delta Change", f"{delta_change:+.4f}", delta=f"{delta_change:+.4f}")
    
    # Check violation
    has_violation, violation_qty, violation_reason = check_violation(net_delta, base_delta)
    
    st.markdown("---")
    
    if has_violation:
        st.markdown('<div class="violation-box">', unsafe_allow_html=True)
        st.error("🚨 **DELTA VIOLATION DETECTED!**")
        
        st.write(f"**Reason:** {violation_reason}")
        st.write(f"**Calculation:** |{net_delta:.4f} - ({base_delta:.4f})| = |{net_delta - base_delta:.4f}| = **{violation_qty:.4f}**")
        
        st.write(f"### **Violation Quantity: {violation_qty:.4f}**")
        
        # Calculate penalty
        penalty_raw, final_penalty, gst, total_penalty = calculate_penalty(violation_qty, stock_price)
        
        st.markdown("---")
        st.markdown("### 💰 Penalty Breakdown")
        
        col_pen1, col_pen2 = st.columns([1, 1])
        
        with col_pen1:
            st.code(f"""
Base Delta (Old): {base_delta:.4f}
Net Delta (New):  {net_delta:.4f}

Delta Change = {net_delta:.4f} - ({base_delta:.4f})
             = {net_delta - base_delta:.4f}

Violation Qty = |{net_delta - base_delta:.4f}|
              = {violation_qty:.4f}

Underlying Price: ₹{stock_price:,.2f}
            """)
        
        with col_pen2:
            st.code(f"""
Raw Penalty Calculation:
= {violation_qty:.4f} × ₹{stock_price:.2f} × 1%
= ₹{penalty_raw:,.2f}

Final Penalty: ₹{final_penalty:,.2f}
(Min: ₹5,000 | Max: ₹1,00,000)

GST (18%): ₹{gst:,.2f}

───────────────────────────
TOTAL: ₹{total_penalty:,.2f}
            """)
        
        st.markdown(f"## 🔴 **TOTAL PENALTY: ₹{total_penalty:,.2f}**")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="safe-box">', unsafe_allow_html=True)
        st.success("✅ **NO VIOLATION DETECTED**")
        
        if base_delta == 0 and net_delta == 0:
            st.write("No positions to evaluate.")
        elif net_delta != base_delta:
            st.info(f"ℹ️ {violation_reason} - Delta has decreased or this could be a **passive change** (market movement).")
        else:
            st.write("Positions are unchanged.")
        
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("👆 Add positions in both OLD and NEW sections to calculate violations")

# Example scenarios
st.markdown("---")
with st.expander("📚 Example: Sign Change Violation (from your screenshot)", expanded=False):
    st.markdown("""
    ### Example: Delta Sign Change Violation
    
    **OLD POSITION (Base Delta = -2732.9080):**
    - Net Delta is **negative**
    
    **NEW POSITION (Net Delta = +1570.7040):**
    - Net Delta is now **positive**
    
    **VIOLATION CALCULATION:**
    - Base Delta (Old) = -2732.9080
    - Net Delta (New) = +1570.7040
    - Delta Change = 1570.7040 - (-2732.9080) = +4303.6120
    - **Violation Quantity = |4303.6120| = 4303.6120**
    
    This is a violation because:
    1. The sign changed from **negative to positive**
    2. The absolute difference is used: |-2732.9080 + 1570.7040| = |4303.6120|
    
    Note: The calculator always uses the **absolute value** of the delta change when calculating violation quantity.
    """)

with st.expander("📚 Example: Bandhan Bank Case", expanded=False):
    st.markdown("""
    ### Real Example: BANDHANBNK Delta Violation
    
    **Dec 4, 2025 EOD (OLD POSITION - Base Delta = 25.632):**
    
    | Type | Direction | Quantity | Delta | Position Delta |
    |------|-----------|----------|-------|----------------|
    | Call Option (170CE) | Long | 7200 | 0.02323 | 167.256 |
    | Call Option (180CE) | Short | 25200 | 0.00562 | -141.624 |
    | **NET DELTA** | | | | **25.632** |
    
    **Dec 5, 2025 EOD (NEW POSITION - After closing some short calls):**
    
    | Type | Direction | Quantity | Delta | Position Delta |
    |------|-----------|----------|-------|----------------|
    | Call Option (170CE) | Long | 7200 | 0.02323 | 167.256 |
    | Call Option (180CE) | Short | 3600 | 0.00562 | -20.232 |
    | **NET DELTA** | | | | **147.024** |
    
    **VIOLATION CALCULATION:**
    - Base Delta (Old) = 25.632
    - Net Delta (New) = 147.024
    - Delta Change = 147.024 - 25.632 = +121.392
    - Violation Quantity = |121.392| = **121.392**
    - Underlying Price = ₹135.47
    - Raw Penalty = 121.392 × 135.47 × 1% = **₹164.44**
    - Final Penalty = **₹5,000** (minimum applied)
    - GST (18%) = **₹900**
    - **TOTAL PENALTY = ₹5,900**
    """)

# Footer
st.markdown("---")
st.caption("💡 This calculator follows NSE's delta violation penalty rules for F&O contracts in ban period. Violation quantity is always calculated as the absolute value of (Net Delta - Base Delta).")