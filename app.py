import streamlit as st
import base64
import json
import re

# Optional: Try importing OpenAI and streamlit_image_select
try:
    from openai import OpenAI
    client = OpenAI()
except Exception:
    client = None

try:
    from streamlit_image_select import image_select
    HAS_IMAGE_SELECT = True
except ImportError:
    HAS_IMAGE_SELECT = False

st.set_page_config(page_title="SSG Shop Drawing Generator", layout="wide")

# =========================================================
# 1. INITIAL SESSION STATE RESET
# =========================================================
if "app_initialized" not in st.session_state:
    st.session_state["app_initialized"] = True
    st.session_state["p1_w"] = 0.0
    st.session_state["p1_h"] = 0.0
    st.session_state["p2_w"] = 0.0
    st.session_state["p2_h"] = 0.0
    st.session_state["p3_w"] = 0.0
    st.session_state["p3_h"] = 0.0

# =========================================================
# 2. HELPER FUNCTIONS & VISION API
# =========================================================
def calculate_scaled_bounds(real_w, real_h, max_w=400, max_h=400):
    """Safely calculates bounding dimensions without ZeroDivisionError."""
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

def extract_measurements_from_sketch(uploaded_file):
    """Converts uploaded image to Base64 and extracts panel dimensions via OpenAI GPT-4o."""
    if not client:
        raise ValueError("OpenAI client is not initialized. Ensure OPENAI_API_KEY is configured.")
        
    bytes_data = uploaded_file.getvalue()
    base64_image = base64.b64encode(bytes_data).decode("utf-8")
    
    prompt = """
    You are an expert glazier assistant reading installer hand sketches for shower screens.
    Extract the panel measurements in millimeters (mm).
    
    Return ONLY a valid raw JSON object matching this structure:
    {
      "p1_w": float or 0.0,
      "p1_h": float or 0.0,
      "p2_w": float or 0.0,
      "p2_h": float or 0.0,
      "p3_w": float or 0.0,
      "p3_h": float or 0.0
    }
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                    }
                ]
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.0
    )
    
    raw_json = response.choices[0].message.content
    return json.loads(raw_json)


# =========================================================
# 3. TOP NAVIGATION & DIAGRAM ICON SELECTION
# =========================================================
st.title("SSG Shop Drawing Generator")

st.subheader("1. Select Shower Screen Shape:")

if HAS_IMAGE_SELECT:
    selected_icon = image_select(
        label="Click layout diagram:",
        images=[
            "https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/solid/rectangle.svg", 
            "https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/solid/table-columns.svg", 
            "https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/solid/vector-square.svg" 
        ],
        captions=["Single Fixed Panel", "2-Panel Inline", "3-Panel Corner / L-Shape"],
        index=0,
        use_container_width=False,
        key="layout_icon_select"
    )
    if selected_icon == "Single Fixed Panel":
        layout_style = "Single Fixed Panel"
    elif selected_icon == "2-Panel Inline":
        layout_style = "2-Panel Inline (Door + Return)"
    else:
        layout_style = "3-Panel Corner / L-Shape"
else:
    # Fallback standard selector if pip library is missing
    layout_style = st.radio(
        "Shower Screen Style:",
        ["Single Fixed Panel", "2-Panel Inline (Door + Return)", "3-Panel Corner / L-Shape"],
        horizontal=True
    )

st.divider()

# =========================================================
# 4. TOP DYNAMIC INPUT MENUS (TABS & EXPANDERS)
# =========================================================
tab_manual, tab_vision = st.tabs(["2. Input Manual Measurements", "3. Auto-Fill from Installer Sketch"])

with tab_manual:
    # Set expanders to collapsed (expanded=False) for max workspace
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

    # Global options
    with st.expander("Global Hardware & Glass Options", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Hole Size (mm):", [10, 12, 14, 16, 20], key="hole_diameter")
        with col2:
            st.selectbox("Hardware Finish:", ["Chrome", "Black", "Brushed Brass", "Satin"], key="hardware_finish")


with tab_vision:
    uploaded_sketch = st.file_uploader("Upload Installer Sketch (JPG/PNG)", type=["jpg", "jpeg", "png"])
    
    if uploaded_sketch:
        st.success("Sketch uploaded. Ready to extract data.")
        if st.button("Extract Data from Sketch"):
            with st.spinner("Analyzing sketch with Vision API..."):
                try:
                    extracted_data = extract_measurements_from_sketch(uploaded_sketch)
                    
                    st.session_state["p1_w"] = float(extracted_data.get("p1_w", 0.0))
                    st.session_state["p1_h"] = float(extracted_data.get("p1_h", 0.0))
                    st.session_state["p2_w"] = float(extracted_data.get("p2_w", 0.0))
                    st.session_state["p2_h"] = float(extracted_data.get("p2_h", 0.0))
                    st.session_state["p3_w"] = float(extracted_data.get("p3_w", 0.0))
                    st.session_state["p3_h"] = float(extracted_data.get("p3_h", 0.0))
                    
                    st.toast("Measurements successfully extracted!", icon="✅")
                    st.rerun()
                except Exception as err:
                    st.error(f"Extraction failed: {str(err)}")

st.divider()

# =========================================================
# 5. SHOP DRAWING DISPLAY AREA
# =========================================================
st.subheader("Shop Drawing Layout")
st.write(f"**Selected Style:** {layout_style}")
st.write(f"**Hardware Finish:** {st.session_state.get('hardware_finish', 'Chrome')}")

# Active panel breakdown display
detail_tabs = ["Panel 1 Details"]
if layout_style in ["2-Panel Inline (Door + Return)", "3-Panel Corner / L-Shape"]:
    detail_tabs.append("Panel 2 Details")
if layout_style == "3-Panel Corner / L-Shape":
    detail_tabs.append("Panel 3 Details")

tabs_obj = st.tabs(detail_tabs)

with tabs_obj[0]:
    st.write(f"**P1 - Fixed/Return:** {st.session_state.p1_w}mm (W) x {st.session_state.p1_h}mm (H)")

if len(detail_tabs) > 1:
    with tabs_obj[1]:
        st.write(f"**P2 - Center Door:** {st.session_state.p2_w}mm (W) x {st.session_state.p2_h}mm (H)")

if len(detail_tabs) > 2:
    with tabs_obj[2]:
        st.write(f"**P3 - Right Fixed:** {st.session_state.p3_w}mm (W) x {st.session_state.p3_h}mm (H)")

# Safe bounds check prior to drawing calculation
if st.session_state.p1_w > 0 and st.session_state.p1_h > 0:
    ox, oy, pw, ph = calculate_scaled_bounds(st.session_state.p1_w, st.session_state.p1_h)
    st.success(f"Rendering Drawing Canvas (Scaled Bounds: {pw:.0f}x{ph:.0f})...")
else:
    st.warning("Enter valid panel dimensions (> 0) above or upload a sketch to generate the drawing canvas.")