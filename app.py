# app.py
import streamlit as st
import json
from sketch_parser import HybridSketchEngine, ParsedGlassPanel

st.set_page_config(
    page_title="Cheapest Shower Screens - Self-Learning Sketch Parser",
    page_icon="📐",
    layout="wide"
)

st.title("Shower Screen Hybrid Sketch-to-CAD Parser")
st.write("Upload a site sketch. The system parses dimensions using local vision memory or Vision LLM, placing hardware cutouts adaptively.")

# Initialize Hybrid Engine
@st.cache_resource
def load_engine():
    return HybridSketchEngine()

engine = load_engine()

# Initialize Session State
if "panel" not in st.session_state:
    st.session_state["panel"] = None
if "engine_used" not in st.session_state:
    st.session_state["engine_used"] = ""
if "crops_data" not in st.session_state:
    st.session_state["crops_data"] = []

# Sidebar API Key & File Upload
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("OpenAI API Key (Optional for Fallback)", type="password")
    if api_key:
        engine.api_key = api_key

    st.markdown("---")
    st.header("Upload Sketch")
    uploaded_file = st.file_uploader("Choose sketch image", type=["jpg", "png", "jpeg"])
    
    if uploaded_file is not None:
        if st.button("Process / Reset Sketch", use_container_width=True):
            st.session_state["panel"] = None

if uploaded_file is not None:
    image_bytes = uploaded_file.getvalue()

    if st.session_state["panel"] is None:
        with st.spinner("Analyzing sketch with hybrid computer vision..."):
            panel, engine_used, crops_data = engine.process_sketch(image_bytes)
            st.session_state["panel"] = panel
            st.session_state["engine_used"] = engine_used
            st.session_state["crops_data"] = crops_data

    panel: ParsedGlassPanel = st.session_state["panel"]
    engine_used = st.session_state["engine_used"]
    crops_data = st.session_state["crops_data"]

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.subheader("Uploaded Site Sketch")
        st.image(image_bytes, use_column_width=True)
        if "Local" in engine_used:
            st.success(f" Parsed via: **{engine_used}**")
        else:
            st.info(f" Parsed via: **{engine_used}**")

    with col_right:
        st.subheader("Geometry Overrides & Specs")
        
        c_w, c_h = st.columns(2)
        with c_w:
            new_width = st.number_input("Width (mm)", value=float(panel.width_mm), step=1.0)
        with c_h:
            new_height = st.number_input("Height (mm)", value=float(panel.height_mm), step=1.0)

        glass_type = st.selectbox(
            "Glass Specification", 
            ["10mm Clear Toughened", "10mm Extra Clear / Low Iron", "10mm Frosted Toughened"]
        )

        if new_width != panel.width_mm or new_height != panel.height_mm or glass_type != panel.glass_type:
            panel.width_mm = new_width
            panel.height_mm = new_height
            panel.glass_type = glass_type
            panel.cutouts = engine.auto_place_hardware(new_width, new_height)
            st.session_state["panel"] = panel

        st.markdown("---")
        m1, m2, m3 = st.columns(3)
        m1.metric("Area", f"{panel.area_m2:.2f} m²")
        m2.metric("Weight", f"{panel.weight_kg:.1f} kg")
        m3.metric("Cutouts", f"{len(panel.cutouts)} Items")

        st.markdown("---")
        st.subheader("Hardware & Placement Adjustments")
        
        top_hinge = next((c for c in panel.cutouts if c.cutout_type == "hinge_top"), None)
        bot_hinge = next((c for c in panel.cutouts if c.cutout_type == "hinge_bottom"), None)

        cur_top_offset = top_hinge.y_offset_mm if top_hinge else 250.0
        cur_bot_offset = (panel.height_mm - bot_hinge.y_offset_mm) if bot_hinge else 250.0

        col_h1, col_h2 = st.columns(2)
        with col_h1:
            adj_top = st.number_input("Top Hinge Offset (mm)", value=float(cur_top_offset), step=5.0)
        with col_h2:
            adj_bot = st.number_input("Bottom Hinge Offset (mm)", value=float(cur_bot_offset), step=5.0)

        if st.button("Train Hardware Placement Model"):
            engine.hardware_ml.learn(
                height_mm=panel.height_mm,
                width_mm=panel.width_mm,
                weight_kg=panel.weight_kg,
                actual_top_mm=adj_top,
                actual_bot_mm=adj_bot
            )
            panel.cutouts = engine.auto_place_hardware(panel.width_mm, panel.height_mm)
            st.session_state["panel"] = panel
            st.success("Updated `hardware_model.pkl`! Hardware placement rules refined.")

        st.markdown("---")
        st.subheader("Teach Visual Handwriting Store")
        st.write("If the local parser struggled, label these cropped regions to update `sketch_memory.pkl`:")

        for idx, item in enumerate(crops_data[:3]):
            cr_col1, cr_col2 = st.columns([1, 2])
            with cr_col1:
                st.image(item["crop"], caption=f"Crop #{idx+1}", width=90)
            with cr_col2:
                lbl = st.text_input(f"Label #{idx+1}", value=str(int(item["val"])), key=f"crop_lbl_{idx}")
                if st.button(f"Save Handwriting #{idx+1}", key=f"btn_save_{idx}"):
                    engine.style_memory.train_symbol(item["crop"], lbl)
                    st.success(f"Visual pattern saved into local memory as '{lbl}'.")

        st.markdown("---")
        st.subheader("Exportable CAD Job Payload")
        payload = panel.to_dict()
        st.json(payload)

        st.download_button(
            label="Download CAD Job File (JSON)",
            data=json.dumps(payload, indent=4),
            file_name=f"shower_panel_{panel.panel_id}.json",
            mime="application/json",
            use_container_width=True
        )
else:
    st.info("Upload a sketch image from the sidebar to start parsing.")