import streamlit as st
# Requires installing image select: pip install streamlit-image-select
from streamlit_image_select import image_select
import time

st.set_page_config(page_title="SSG Shop Drawing Generator", layout="wide")

# --- INITIAL SESSION STATE RESET ---
if "app_initialized" not in st.session_state:
    st.session_state["app_initialized"] = True
    # Initial measurements set to 0.0 (and not saved, so they reset on restart)
    st.session_state["p1_w"] = 0.0
    st.session_state["p1_h"] = 0.0
    st.session_state["p2_w"] = 0.0
    st.session_state["p2_h"] = 0.0
    st.session_state["p3_w"] = 0.0
    st.session_state["p3_h"] = 0.0

# =========================================================
# HELPER: SAFE CANVAS CALCULATIONS (Prevents ZeroDivisionError)
# =========================================================
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
st.write("Generated from measuring tool 'app.py'")

# =========================================================
# TOP CONFIGURATION BAR
# =========================================================
st.divider()
st.subheader("1. Select Shower Screen Shape:")

# Using streamlit-image-select for visual selection instead of a dropdown
# Icons: Single Panel (Rect), Inline (2-Panel), Corner (3-Panel / L-Shape)
selected_icon = image_select(
    label="Choose a design layout:",
    images=[
        "https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/solid/rectangle.svg",  # Represents Single Panel
        "https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/solid/table-columns.svg", # Represents Inline (2)
        "https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/solid/vector-square.svg" # Represents Corner (3/L)
    ],
    captions=["Single Fixed Panel", "2-Panel Inline", "3-Panel Corner / L-Shape"],
    index=0,  # Default to Single Fixed Panel
    use_container_width=False,
    key="layout_icon_select"
)

# Map the selected icon caption back to the internal layout name
if selected_icon == "Single Fixed Panel":
    layout_style = "Single Fixed Panel"
elif selected_icon == "2-Panel Inline":
    layout_style = "2-Panel Inline (Door + Return)"
else:
    layout_style = "3-Panel Corner / L-Shape"

st.divider()

# =========================================================
# DYNAMIC PANEL MENUS & SKETCH UPLOAD
# =========================================================
# Use tabs to organize the remaining inputs, making them compact
tab_input, tab_upload = st.tabs(["2. Input Manual Measurements", "3. Auto-Fill from Installer Sketch"])

with tab_input:
    # Set expanders to collapsed (expanded=False) for cleaner start
    with st.expander("Panel 1 (Fixed / Return) – Configuration", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.number_input("P1 Width (mm)", min_value=0.0, key="p1_w")
            st.number_input("P1 Height (mm)", min_value=0.0, key="p1_h")
        with col2:
            st.selectbox("P1 Bracket Edge", ["None", "Left", "Right", "Both"], key="p1_bracket_edge")
            st.number_input("P1 Bracket Hole Dia (mm)", min_value=0.0, key="p1_bracket_dia")
        with col3:
            st.number_input("P1 Hole Top Offset (mm)", min_value=0.0, key="p1_top_off")
            st.number_input("P1 Hole Bottom Offset (mm)", min_value=0.0, key="p1_bot_off")

    # Dynamic Panel 2: Only show for multi-panel styles
    if layout_style in ["2-Panel Inline (Door + Return)", "3-Panel Corner / L-Shape"]:
        with st.expander("Panel 2 (Center / Door Panel) – Configuration", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.number_input("P2 Width (mm)", min_value=0.0, key="p2_w")
                st.number_input("P2 Height (mm)", min_value=0.0, key="p2_h")
            with col2:
                st.selectbox("P2 Hinge Edge", ["Left", "Right"], key="p2_hinge_edge")
                st.number_input("P2 Hinge Top Offset (mm)", min_value=0.0, key="p2_hinge_top")
            with col3:
                st.number_input("P2 Hinge Bottom Offset (mm)", min_value=0.0, key="p2_hinge_bot")
                st.selectbox("P2 Door Knob Edge", ["Left", "Right"], key="p2_knob_edge")

    # Dynamic Panel 3: Only show for 3-Panel Corner/L-Shape style
    if layout_style == "3-Panel Corner / L-Shape":
        with st.expander("Panel 3 (Right Fixed Panel) – Configuration", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.number_input("P3 Width (mm)", min_value=0.0, key="p3_w")
            with col2:
                st.number_input("P3 Height (mm)", min_value=0.0, key="p3_h")

    # Global hardware setting (preserved)
    st.divider()
    with st.expander("Global hardware Options", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Hole Size (mm):", [10, 12, 14, 16, 20], key="hole_diameter")
        with col2:
            st.selectbox("Hardware Finish:", ["Chrome", "Black", "Brushed Brass", "Satin"], key="hardware_finish")


with tab_upload:
    uploaded_sketch = st.file_uploader("Upload Installer Sketch (JPG/PNG)", type=["jpg", "jpeg", "png"])
    if uploaded_sketch:
        st.success("Sketch uploaded. Ready to extract data.")
        st.warning("Vision API extraction not yet implemented.")
        # if st.button("Extract Data from Sketch"):
        #     st.toast("Calling Vision API...", icon="⌛")
        #     time.sleep(1) # Simulation
        #     # Example data update (requires actual API implementation):
        #     # st.session_state["p1_w"] = 950.0
        #     # st.session_state["p1_h"] = 2100.0
        #     # st.rerun()

st.divider()

# =========================================================
# MAIN OUTPUT & SHOP DRAWING AREA
# =========================================================
st.subheader("Shop Drawing Layout")
st.write(f"**Layout Selected:** {layout_style}")
st.write(f"**Hardware Finish:** {st.session_state.get('hardware_finish', 'Chrome')}")

# Dynamic active panel breakdown
tab_p1_details, tab_p2_details, tab_p3_details = st.tabs(["Panel 1 Details", "Panel 2 Details", "Panel 3 Details"])

with tab_p1_details:
    st.write(f"**P1 - Fixed/Return:** {st.session_state.p1_w}mm (W) x {st.session_state.p1_h}mm (H)")

if layout_style in ["2-Panel Inline (Door + Return)", "3-Panel Corner / L-Shape"]:
    with tab_p2_details:
        st.write(f"**P2 - Center Door:** {st.session_state.p2_w}mm (W) x {st.session_state.p2_h}mm (H)")

if layout_style == "3-Panel Corner / L-Shape":
    with tab_p3_details:
        st.write(f"**P3 - Right Fixed:** {st.session_state.p3_w}mm (W) x {st.session_state.p3_h}mm (H)")

# Safe drawing calculation check
if st.session_state.p1_w > 0 and st.session_state.p1_h > 0:
    ox, oy, pw, ph = calculate_scaled_bounds(st.session_state.p1_w, st.session_state.p1_h)
    st.success(f"Rendering Drawing Canvas (Scaled Bounds: {pw:.0f}x{ph:.0f})...")
    # Your canvas rendering logic goes here
    # Example: generate_pdf(ox, oy, pw, ph)
else:
    st.warning("Enter valid dimensions (> 0) above to generate the drawing canvas.")