import streamlit as st

st.set_page_config(page_title="SSG Shop Drawing Generator", layout="wide")

# --- INITIAL SESSION STATE RESET ---
if "app_initialized" not in st.session_state:
    st.session_state["app_initialized"] = True
    st.session_state["p1_w"] = 0.0
    st.session_state["p1_h"] = 0.0
    st.session_state["p2_w"] = 0.0
    st.session_state["p2_h"] = 0.0
    st.session_state["p3_w"] = 0.0
    st.session_state["p3_h"] = 0.0

# --- HELPER: SAFE CANVAS CALCULATIONS ---
def calculate_scaled_bounds(real_w, real_h, max_w=400, max_h=400):
    if float(real_h) <= 0 or float(real_w) <= 0:
        return 0, 0, max_w, max_h
    aspect = float(real_w) / float(real_h)
    if aspect > 1:
        p_w = max_w
        p_h = max_w / aspect
    else:
        p_h = max_h
        p_w = max_h * aspect
    return 0, 0, p_w, p_h


st.title("SSG Shop Drawing Generator")

# =========================================================
# TOP CONFIGURATION BAR
# =========================================================
top_col1, top_col2 = st.columns([2, 2])

with top_col1:
    layout_style = st.selectbox(
        "Select Shower Screen Layout Style:",
        ["Single Fixed Panel", "2-Panel Inline (Door + Return)", "3-Panel Corner / L-Shape"],
        key="layout_style"
    )

with top_col2:
    uploaded_sketch = st.file_uploader("Upload Installer Sketch (JPG/PNG)", type=["jpg", "jpeg", "png"])
    if uploaded_sketch:
        st.success("Sketch uploaded.")

st.divider()

# =========================================================
# TOP DYNAMIC PANEL MENUS
# =========================================================
st.subheader("Panel Measurements & Options")

# Determine column count dynamically based on selected layout
if layout_style == "Single Fixed Panel":
    cols = st.columns(1)
elif layout_style == "2-Panel Inline (Door + Return)":
    cols = st.columns(2)
else:
    cols = st.columns(3)

# --- PANEL 1 MENU (Column 1) ---
with cols[0]:
    with st.expander("Panel 1 (Fixed / Return)", expanded=True):
        st.number_input("P1 Width (mm)", min_value=0.0, key="p1_w")
        st.number_input("P1 Height (mm)", min_value=0.0, key="p1_h")
        st.selectbox("P1 Bracket Edge", ["None", "Left", "Right", "Both"], key="p1_bracket_edge")
        st.number_input("P1 Bracket Hole Dia (mm)", min_value=0.0, key="p1_bracket_dia")
        st.number_input("P1 Hole Top Offset (mm)", min_value=0.0, key="p1_top_off")
        st.number_input("P1 Hole Bottom Offset (mm)", min_value=0.0, key="p1_bot_off")

# --- PANEL 2 MENU (Column 2 - If applicable) ---
if layout_style in ["2-Panel Inline (Door + Return)", "3-Panel Corner / L-Shape"]:
    with cols[1]:
        with st.expander("Panel 2 (Center / Door Panel)", expanded=True):
            st.number_input("P2 Width (mm)", min_value=0.0, key="p2_w")
            st.number_input("P2 Height (mm)", min_value=0.0, key="p2_h")
            st.selectbox("P2 Hinge Edge", ["Left", "Right"], key="p2_hinge_edge")
            st.number_input("P2 Hinge Top Offset (mm)", min_value=0.0, key="p2_hinge_top")
            st.number_input("P2 Hinge Bottom Offset (mm)", min_value=0.0, key="p2_hinge_bot")
            st.selectbox("P2 Door Knob Edge", ["Left", "Right"], key="p2_knob_edge")

# --- PANEL 3 MENU (Column 3 - If applicable) ---
if layout_style == "3-Panel Corner / L-Shape":
    with cols[2]:
        with st.expander("Panel 3 (Right Fixed Panel)", expanded=True):
            st.number_input("P3 Width (mm)", min_value=0.0, key="p3_w")
            st.number_input("P3 Height (mm)", min_value=0.0, key="p3_h")

st.divider()

# =========================================================
# MAIN OUTPUT & SHOP DRAWING AREA
# =========================================================
st.subheader("Panel Quantity Breakdown")
st.write(f"• **P1 - Left Fixed/Return Panel:** {st.session_state.p1_w}mm x {st.session_state.p1_h}mm")

if layout_style in ["2-Panel Inline (Door + Return)", "3-Panel Corner / L-Shape"]:
    st.write(f"• **P2 - Center Door Panel:** {st.session_state.p2_w}mm x {st.session_state.p2_h}mm")

if layout_style == "3-Panel Corner / L-Shape":
    st.write(f"• **P3 - Right Fixed Panel:** {st.session_state.p3_w}mm x {st.session_state.p3_h}mm")

# Safe drawing calculation check
if st.session_state.p1_w > 0 and st.session_state.p1_h > 0:
    ox, oy, pw, ph = calculate_scaled_bounds(st.session_state.p1_w, st.session_state.p1_h)
    st.success("Panel dimensions valid. Rendering drawing...")
else:
    st.warning("Enter panel width and height greater than 0 to generate shop drawing bounds.")