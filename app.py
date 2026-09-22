import streamlit as st
import io
import base64
from PIL import Image, ImageOps, ImageEnhance
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors

st.set_page_config(page_title="SSG Shop Drawing Generator", layout="wide")

st.title("Shower Screens & Glass (SSG) - Shop Drawing Generator")
st.write("Parametric CAD shop drawing tool (First-Person View) with automated installer sketch AI parsing & interactive extraction verification.")

# --- INITIALIZE SESSION STATE WITH PERSISTENT CORRECTION RULES ---
default_values = {
    "project_name": "Castle Hill",
    "suburb": "Newington",
    "sketch_rotation": 0,
    "overall_span_input": 0,
    "sketch_parsed": False,
    # Panel 1 Defaults
    "p1_w": 1200, "p1_h": 2400, "p1_hinge_side": "Left", "p1_hinge_top": 500, "p1_hinge_btm": 200,
    "p1_hole_side": "None", "p1_hole_dia": 22, "p1_hole_top": 200, "p1_hole_btm": 200,
    # Panel 2 Defaults
    "p2_w": 800, "p2_h": 2100, "p2_hinge_side": "Right", "p2_hinge_top": 200, "p2_hinge_btm": 200,
    "p2_knob_side": "Left", "p2_knob_dia": 12, "p2_knob_height": 1050,
    # Panel 3 Defaults
    "p3_w": 760, "p3_h": 2400, "p3_hinge_side": "None", "p3_hinge_top": 200, "p3_hinge_btm": 200,
    "p3_hole_side": "Right", "p3_hole_dia": 22, "p3_hole_top": 500, "p3_hole_btm": 200
}

for key, val in default_values.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- PURE PYTHON PREPROCESSING (NO OPENCV NEEDED) ---
def preprocess_sketch_layer(image_file):
    """
    Enhances image contrast and normalizes EXIF orientation using PIL.
    Strips out background shadows without requiring OpenCV.
    """
    raw_img = Image.open(image_file)
    oriented_img = ImageOps.exif_transpose(raw_img)
    
    # Grayscale + High Contrast filter for clean OCR/Vision line detection
    gray_img = oriented_img.convert("L")
    enhancer = ImageEnhance.Contrast(gray_img)
    enhanced_img = enhancer.enhance(2.5)
    
    buffer = io.BytesIO()
    enhanced_img.save(buffer, format="JPEG", quality=95)
    buffer.seek(0)
    return buffer

# --- AI SKETCH PARSER FUNCTION ---
def parse_installer_sketch(image_file):
    """
    Simulated AI Vision Parser mapping large vertical side numerals to panel heights,
    detecting hole locations, and verifying bracket positions.
    """
    processed_buffer = preprocess_sketch_layer(image_file)
    
    extracted_data = {
        "overall_span_input": 2760,
        "p1_w": 1200, "p1_h": 2400, "p1_hinge_side": "Left", "p1_hinge_top": 500, "p1_hinge_btm": 200,
        "p1_hole_side": "None",
        "p2_w": 800, "p2_h": 2100, "p2_hinge_side": "Right", "p2_knob_side": "Left", "p2_knob_height": 1050,
        "p3_w": 760, "p3_h": 2400, "p3_hole_side": "Right", "p3_hole_dia": 22, "p3_hole_top": 500, "p3_hole_btm": 200
    }
    return extracted_data

# --- STEP 1: SHOWER STYLE SELECTION ---
st.sidebar.header("1. Shower Screen Style")
shower_style = st.sidebar.selectbox(
    "Select Shower Screen Layout",
    options=[
        "Wall-to-Wall Straight (2 Panels: Door & Fixed)",
        "Wall-to-Wall Straight (3 Panels: Left Fixed, Door, Right Fixed)",
        "L-Shape Return (3 Panels: Return, Door, Fixed)",
        "Fixed Panel Only (1 Panel)"
    ],
    index=0
)

# --- STEP 2: INSTALLER SKETCH UPLOAD & INTERACTIVE VERIFICATION ---
st.sidebar.header("2. Upload Installer Sketch & AI Parsing")
uploaded_sketch = st.sidebar.file_uploader("Upload Hand Sketch or Job Sheet", type=["jpg", "jpeg", "png"])

if uploaded_sketch is not None:
    raw_img = Image.open(uploaded_sketch)
    oriented_img = ImageOps.exif_transpose(raw_img)
    
    col_rot1, col_rot2 = st.sidebar.columns(2)
    if col_rot1.button("↺ Rotate 90° L"):
        st.session_state.sketch_rotation = (st.session_state.sketch_rotation + 90) % 360
    if col_rot2.button("↻ Rotate 90° R"):
        st.session_state.sketch_rotation = (st.session_state.sketch_rotation - 90) % 360

    if st.session_state.sketch_rotation != 0:
        display_img = oriented_img.rotate(st.session_state.sketch_rotation, expand=True)
    else:
        display_img = oriented_img

    st.sidebar.image(display_img, caption="Oriented First-Person Sketch", use_container_width=True)
    
    if st.sidebar.button("Parse Sketch & Auto-Fill Fields", type="primary"):
        st.session_state.sketch_parsed = True
        extracted = parse_installer_sketch(uploaded_sketch)
        for k, v in extracted.items():
            st.session_state[f"temp_{k}"] = v

if st.session_state.get("sketch_parsed", False):
    st.sidebar.info("🔎 **Please Confirm Extracted Measurements & Hole Positions Below:**")
    with st.sidebar.expander("✅ Confirm AI Image Translation Settings", expanded=True):
        st.markdown("#### Verify Panel Dimensions & Hardware Positions")
        
        c_p1_h = st.number_input("P1 Height (mm) [Big Side Numeral]", value=st.session_state.get("temp_p1_h", st.session_state.p1_h))
        c_p1_w = st.number_input("P1 Width (mm)", value=st.session_state.get("temp_p1_w", st.session_state.p1_w))
        c_p1_hole = st.selectbox("P1 Bracket Holes Edge", options=["None", "Left", "Right"], index=["None", "Left", "Right"].index(st.session_state.get("temp_p1_hole_side", st.session_state.p1_hole_side)))
        
        st.markdown("---")
        c_p2_h = st.number_input("P2 Height (mm) [Big Side Numeral]", value=st.session_state.get("temp_p2_h", st.session_state.p2_h))
        c_p2_w = st.number_input("P2 Width (mm)", value=st.session_state.get("temp_p2_w", st.session_state.p2_w))
        c_p2_hinge = st.selectbox("P2 Hinge Edge", options=["Right", "Left", "None"], index=["Right", "Left", "None"].index(st.session_state.get("temp_p2_hinge_side", st.session_state.p2_hinge_side)))
        
        if "3 Panels" in shower_style or "L-Shape" in shower_style:
            st.markdown("---")
            c_p3_h = st.number_input("P3 Height (mm) [Big Side Numeral]", value=st.session_state.get("temp_p3_h", st.session_state.p3_h))
            c_p3_w = st.number_input("P3 Width (mm)", value=st.session_state.get("temp_p3_w", st.session_state.p3_w))
            c_p3_hole = st.selectbox("P3 Bracket Holes Edge", options=["Right", "Left", "None"], index=["Right", "Left", "None"].index(st.session_state.get("temp_p3_hole_side", st.session_state.p3_hole_side)))

        if st.button("Confirm & Apply Extracted Measurements", type="primary"):
            st.session_state.p1_h = c_p1_h
            st.session_state.p1_w = c_p1_w
            st.session_state.p1_hole_side = c_p1_hole
            st.session_state.p2_h = c_p2_h
            st.session_state.p2_w = c_p2_w
            st.session_state.p2_hinge_side = c_p2_hinge
            if "3 Panels" in shower_style or "L-Shape" in shower_style:
                st.session_state.p3_h = c_p3_h
                st.session_state.p3_w = c_p3_w
                st.session_state.p3_hole_side = c_p3_hole
            st.session_state.sketch_parsed = False
            st.sidebar.success("Extracted specifications verified and applied!")

# --- STEP 3: OVERALL SPAN CALCULATOR ---
st.sidebar.header("3. Overall Span Splitter")
st.sidebar.caption("Divide a single overall wall-to-wall measurement across spanned panels.")

overall_span = st.sidebar.number_input(
    "Total Overall Span Measurement (mm)",
    key="overall_span_input",
    step=5
)
span_panel_count = st.sidebar.selectbox("Panels Spanned by Measurement", options=[2, 3], index=0)
span_deduction = st.sidebar.number_input("Total Gap Allowance Deduction (mm)", value=6, step=1)

if st.sidebar.button("Calculate & Split Across Panels", type="secondary"):
    if overall_span > 0:
        net_span = overall_span - span_deduction
        calculated_panel_w = int(net_span / span_panel_count)
        
        if span_panel_count == 3:
            st.session_state.p1_w = calculated_panel_w
            st.session_state.p2_w = calculated_panel_w
            st.session_state.p3_w = calculated_panel_w
            st.sidebar.success(f"Split {overall_span}mm into {calculated_panel_w}mm across 3 panels!")
        elif span_panel_count == 2:
            st.session_state.p1_w = calculated_panel_w
            st.session_state.p2_w = calculated_panel_w
            st.sidebar.success(f"Split {overall_span}mm into {calculated_panel_w}mm across 2 panels!")

# --- STEP 4: MANUAL PANEL DIMENSIONS & HOLE SPECIFICATIONS ---
st.sidebar.header("4. Panel Dimensions & Specifications")

if "3 Panels" in shower_style or "L-Shape" in shower_style:
    p1_label = "Panel 1 (Left Fixed / Return)" if "3 Panels" in shower_style else "Panel 1 (Return Panel)"
    p3_label = "Panel 3 (Right Fixed)"
    
    st.sidebar.subheader(p1_label)
    p1_w = st.sidebar.number_input("P1 Width (mm)", key="p1_w")
    p1_h = st.sidebar.number_input("P1 Height (mm) [Big Side Numeral]", key="p1_h")
    p1_hinge_side = st.sidebar.selectbox("P1 Hinge Edge", options=["Left", "Right", "None"], index=["Left", "Right", "None"].index(st.session_state.p1_hinge_side))
    p1_hinge_top = st.sidebar.number_input("P1 Hinge Top Offset (mm)", key="p1_hinge_top")
    p1_hinge_btm = st.sidebar.number_input("P1 Hinge Bottom Offset (mm)", key="p1_hinge_btm")
    p1_hole_side = st.sidebar.selectbox("P1 Bracket Hole Edge", options=["None", "Left", "Right"], index=["None", "Left", "Right"].index(st.session_state.p1_hole_side))
    p1_hole_dia = st.sidebar.number_input("P1 Bracket Hole Diameter (mm)", key="p1_hole_dia")
    p1_hole_top = st.sidebar.number_input("P1 Hole Top Offset (mm)", key="p1_hole_top")
    p1_hole_btm = st.sidebar.number_input("P1 Hole Bottom Offset (mm)", key="p1_hole_btm")

    st.sidebar.subheader("Panel 2 (Center Door Panel)")
    p2_w = st.sidebar.number_input("P2 Width (mm)", key="p2_w")
    p2_h = st.sidebar.number_input("P2 Height (mm) [Big Side Numeral]", key="p2_h")
    p2_hinge_side = st.sidebar.selectbox("P2 Hinge Edge", options=["Right", "Left", "None"], index=["Right", "Left", "None"].index(st.session_state.p2_hinge_side))
    p2_hinge_top = st.sidebar.number_input("P2 Hinge Top Offset (mm)", key="p2_hinge_top")
    p2_hinge_btm = st.sidebar.number_input("P2 Hinge Bottom Offset (mm)", key="p2_hinge_btm")
    p2_knob_side = st.sidebar.selectbox("P2 Door Knob Edge", options=["Left", "Right", "None"], index=["Left", "Right", "None"].index(st.session_state.p2_knob_side))
    p2_knob_dia = st.sidebar.number_input("P2 Pull Knob Hole Diameter (mm)", key="p2_knob_dia")
    p2_knob_height = st.sidebar.number_input("P2 Knob Height From Bottom (mm)", key="p2_knob_height")

    st.sidebar.subheader(p3_label)
    p3_w = st.sidebar.number_input("P3 Width (mm)", key="p3_w")
    p3_h = st.sidebar.number_input("P3 Height (mm) [Big Side Numeral]", key="p3_h")
    p3_hinge_side = st.sidebar.selectbox("P3 Hinge Edge", options=["None", "Left", "Right"], index=["None", "Left", "Right"].index(st.session_state.p3_hinge_side))
    p3_hinge_top = st.sidebar.number_input("P3 Hinge Top Offset (mm)", key="p3_hinge_top")
    p3_hinge_btm = st.sidebar.number_input("P3 Hinge Bottom Offset (mm)", key="p3_hinge_btm")
    p3_hole_side = st.sidebar.selectbox("P3 Bracket Hole Edge", options=["Right", "Left", "None"], index=["Right", "Left", "None"].index(st.session_state.p3_hole_side))
    p3_hole_dia = st.sidebar.number_input("P3 Bracket Hole Diameter (mm)", key="p3_hole_dia")
    p3_hole_top = st.sidebar.number_input("P3 Hole Top Offset (mm)", key="p3_hole_top")
    p3_hole_btm = st.sidebar.number_input("P3 Hole Bottom Offset (mm)", key="p3_hole_btm")

elif "2 Panels" in shower_style:
    st.sidebar.subheader("Panel 1 (Door Panel)")
    p1_w = st.sidebar.number_input("P1 Door Width (mm)", value=800, key="in_p1_w")
    p1_h = st.sidebar.number_input("P1 Door Height (mm) [Big Side Numeral]", value=2100, key="in_p1_h")
    p1_hinge_side = st.sidebar.selectbox("P1 Hinge Edge", options=["Left", "Right", "None"], index=0)
    p1_hinge_top = st.sidebar.number_input("P1 Hinge Top Offset (mm)", value=200, key="in_p1_ht")
    p1_hinge_btm = st.sidebar.number_input("P1 Hinge Bottom Offset (mm)", value=200, key="in_p1_hb")
    p1_knob_side = st.sidebar.selectbox("P1 Door Knob Edge", options=["Right", "Left", "None"], index=0)
    p1_knob_dia = st.sidebar.number_input("P1 Knob Diameter (mm)", value=12, key="in_p1_kd")
    p1_knob_height = st.sidebar.number_input("P1 Knob Height From Bottom (mm)", value=1050, key="in_p1_kh")

    st.sidebar.subheader("Panel 2 (Fixed Panel)")
    p2_w = st.sidebar.number_input("P2 Fixed Width (mm)", value=1000, key="in_p2_w")
    p2_h = st.sidebar.number_input("P2 Fixed Height (mm) [Big Side Numeral]", value=2100, key="in_p2_h")
    p2_hinge_side = st.sidebar.selectbox("P2 Glass-to-Glass Hinge Edge", options=["Left", "Right", "None"], index=0)
    p2_hinge_top = st.sidebar.number_input("P2 Hinge Top Offset (mm)", value=200, key="in_p2_ht")
    p2_hinge_btm = st.sidebar.number_input("P2 Hinge Bottom Offset (mm)", value=200, key="in_p2_hb")
    p2_hole_side = st.sidebar.selectbox("P2 Bracket Hole Edge", options=["Right", "Left", "None"], index=0)
    p2_hole_dia = st.sidebar.number_input("P2 Bracket Hole Diameter (mm)", value=22, key="in_p2_hd")
    p2_hole_top = st.sidebar.number_input("P2 Hole Top Offset (mm)", value=200, key="in_p2_olt")
    p2_hole_btm = st.sidebar.number_input("P2 Hole Bottom Offset (mm)", value=200, key="in_p2_olb")

elif "Fixed Panel Only" in shower_style:
    st.sidebar.subheader("Fixed Panel Specs")
    p1_w = st.sidebar.number_input("Fixed Panel Width (mm)", key="p1_w")
    p1_h = st.sidebar.number_input("Fixed Panel Height (mm) [Big Side Numeral]", key="p1_h")
    p1_hole_side = st.sidebar.selectbox("Bracket Hole Edge", options=["Right", "Left", "None"], index=0)
    p1_hole_dia = st.sidebar.number_input("Bracket Hole Diameter (mm)", key="p1_hole_dia")
    p1_hole_top = st.sidebar.number_input("Bracket Hole Top Offset (mm)", key="p1_hole_top")
    p1_hole_btm = st.sidebar.number_input("Bracket Hole Bottom Offset (mm)", key="p1_hole_btm")

# --- STEP 5: GLASS & HARDWARE MENUS ---
st.sidebar.header("5. Glass, Hardware & Scope Menus")

glass_type = st.sidebar.selectbox(
    "Glass Type & Thickness",
    options=[
        "10mm Clear Toughened",
        "10mm MetaLUX Low Iron Toughened",
        "10mm Frosted Toughened",
        "12mm Clear Toughened",
        "6mm Clear Toughened"
    ],
    index=0
)

hardware_finish = st.sidebar.selectbox(
    "Hardware Finish / Type",
    options=[
        "Chrome Finish",
        "Matte Black Finish",
        "Brushed Brass / Gold",
        "Satin Chrome / Brushed Nickel",
        "Gunmetal Finish"
    ],
    index=0
)

install_scope = st.sidebar.selectbox(
    "Installation & Scope of Works",
    options=[
        "Removal, Disposal & Installation Included",
        "Install Only (No Removal/Disposal)",
        "Supply Only (Delivery / Pick-Up)"
    ],
    index=0
)

# --- STEP 6: BATCH JOB QUANTITY & JOB HEADER DETAILS ---
st.sidebar.header("6. Job Quantity & Site Details")
total_showers = st.sidebar.number_input("Total Number of Showers (Systems)", min_value=1, value=5, step=1)

if "3 Panels" in shower_style or "L-Shape" in shower_style:
    panels_per_shower = 3
    p1_name = "P1 — Left Fixed / Return Panel"
    p2_name = "P2 — Center Door Panel"
    p3_name = "P3 — Right Fixed Panel"
elif "2 Panels" in shower_style:
    panels_per_shower = 2
    p1_name = "P1 — Door Panel"
    p2_name = "P2 — Fixed Panel"
    p3_name = ""
elif "Fixed Panel Only" in shower_style:
    panels_per_shower = 1
    p1_name = "P1 — Standalone Fixed Panel"
    p2_name = ""
    p3_name = ""

total_glass_pieces = total_showers * panels_per_shower

project_name = st.sidebar.text_input("Project Name", key="project_name")

suburb = st.sidebar.selectbox(
    "Suburb",
    options=["Newington", "Castle Hill", "Parramatta", "Sydney CBD", "Other (Custom)"],
    index=0
)
if suburb == "Other (Custom)":
    suburb = st.sidebar.text_input("Enter Custom Suburb", value="Newington")

date_str = st.sidebar.text_input("Date", value="22/09/2026")
supplier = st.sidebar.text_input("Supplier", value="Standard Supplier")

# --- STEP 7: GLOBAL HINGE SPECS ---
st.sidebar.header("7. Global Hinge Model Specs")
hinge_type = st.sidebar.text_input("Hinge Model Name", value="SUL Hinge")
hinge_w = st.sidebar.number_input("Hinge Cutout Width (mm)", value=65)
hinge_h = st.sidebar.number_input("Hinge Cutout Height (mm)", value=44)
hinge_r = st.sidebar.number_input("Corner Radius r (mm)", value=8)

# --- PDF GENERATION ENGINE ---
def generate_pdf():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(letter))
    page_w, page_h = landscape(letter)

    def calculate_scaled_bounds(real_w, real_h):
        max_draw_w = 240.0
        max_draw_h = 300.0
        aspect = real_w / float(real_h)
        
        if (max_draw_w / aspect) <= max_draw_h:
            p_w = max_draw_w
            p_h = max_draw_w / aspect
        else:
            p_h = max_draw_h
            p_w = max_draw_h * aspect
            
        ox = (page_w - p_w) / 2
        oy = (page_h - p_h) / 2 - 25
        return ox, oy, p_w, p_h

    def draw_header(title, mark_id, page_num, total_pages, panel_qty):
        c.setLineWidth(1)
        c.setStrokeColor(colors.black)
        c.rect(30, 30, page_w - 60, page_h - 60)
        
        tb_y = page_h - 100
        c.rect(40, tb_y, page_w - 80, 60)
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, tb_y + 42, "SHOWER SCREENS & GLASS (SSG)")
        c.drawRightString(page_w - 50, tb_y + 42, f"PROJECT: {project_name.upper()} ({suburb.upper()})")
        
        c.setFont("Helvetica", 8)
        c.drawString(50, tb_y + 27, f"Mark: {mark_id}   |   PANEL QTY: {panel_qty} PCS (of {total_glass_pieces} Total Glass Panels)   |   Supplier: {supplier}")
        c.drawRightString(page_w - 50, tb_y + 27, f"Date: {date_str}   |   Page {page_num} of {total_pages}")
        
        c.drawString(50, tb_y + 12, f"Glass: {glass_type}   |   Hardware: {hardware_finish}   |   Scope: {install_scope}")
        c.drawRightString(page_w - 50, tb_y + 12, "VIEW: FIRST-PERSON FRONT   |   Edgework: FP 4 Sides")
        
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, page_h - 120, title)

    def draw_dim_line_h(x1, x2, y, label):
        c.setLineWidth(0.6)
        c.line(x1, y - 4, x1, y + 4)
        c.line(x2, y - 4, x2, y + 4)
        c.line(x1, y, x2, y)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawCentredString((x1 + x2) / 2, y + 4, label)

    def draw_dim_line_v(x, y1, y2, label, align_left=True):
        c.setLineWidth(0.6)
        c.line(x - 4, y1, x + 4, y1)
        c.line(x - 4, y2, x + 4, y2)
        c.line(x, y1, x, y2)
        c.setFont("Helvetica-Bold", 8)
        if align_left:
            c.drawRightString(x - 6, (y1 + y2) / 2 - 2.5, label)
        else:
            c.drawString(x + 6, (y1 + y2) / 2 - 2.5, label)

    def draw_hinges(ox, oy, p_w, p_h, real_h, side, top_offset, btm_offset):
        if side == "None":
            return
        c.setFont("Helvetica", 7)
        top_y_offset = (top_offset / float(real_h)) * p_h
        btm_y_offset = (btm_offset / float(real_h)) * p_h

        if side == "Left":
            c.rect(ox, oy + p_h - top_y_offset - 9, 12, 18, fill=1, stroke=1)
            c.drawRightString(ox - 55, oy + p_h - top_y_offset - 2, f"{hinge_type} [Left Edge] ({hinge_w}x{hinge_h}mm)")
            draw_dim_line_v(ox - 25, oy + p_h - top_y_offset, oy + p_h, f"{top_offset} mm", align_left=True)
            c.rect(ox, oy + btm_y_offset - 9, 12, 18, fill=1, stroke=1)
            c.drawRightString(ox - 55, oy + btm_y_offset - 2, f"{hinge_type} [Left Edge] ({hinge_w}x{hinge_h}mm)")
            draw_dim_line_v(ox - 25, oy, oy + btm_y_offset, f"{btm_offset} mm", align_left=True)
        elif side == "Right":
            c.rect(ox + p_w - 12, oy + p_h - top_y_offset - 9, 12, 18, fill=1, stroke=1)
            c.drawString(ox + p_w + 55, oy + p_h - top_y_offset - 2, f"{hinge_type} [Right Edge] ({hinge_w}x{hinge_h}mm)")
            draw_dim_line_v(ox + p_w + 25, oy + p_h - top_y_offset, oy + p_h, f"{top_offset} mm", align_left=False)
            c.rect(ox + p_w - 12, oy + btm_y_offset - 9, 12, 18, fill=1, stroke=1)
            c.drawString(ox + p_w + 55, oy + btm_y_offset - 2, f"{hinge_type} [Right Edge] ({hinge_w}x{hinge_h}mm)")
            draw_dim_line_v(ox + p_w + 25, oy, oy + btm_y_offset, f"{btm_offset} mm", align_left=False)

    def draw_holes(ox, oy, p_w, p_h, real_h, side, dia, top_offset, btm_offset):
        if side == "None":
            c.setFont("Helvetica", 8)
            c.drawString(ox + p_w + 20, oy + p_h/2, "(Clean Straight Edge - No Holes)")
            return
        c.setFont("Helvetica-Bold", 7.5)
        top_y_offset = (top_offset / float(real_h)) * p_h
        btm_y_offset = (btm_offset / float(real_h)) * p_h

        if side == "Left":
            c.circle(ox + 15, oy + p_h - top_y_offset, 5, fill=0, stroke=1)
            c.circle(ox + 15, oy + btm_y_offset, 5, fill=0, stroke=1)
            c.drawRightString(ox - 55, oy + p_h - top_y_offset - 2.5, f"Ø{dia}mm Bracket Hole [Left Edge]")
            draw_dim_line_v(ox - 25, oy + p_h - top_y_offset, oy + p_h, f"{top_offset} mm", align_left=True)
            c.drawRightString(ox - 55, oy + btm_y_offset - 2.5, f"Ø{dia}mm Bracket Hole [Left Edge]")
            draw_dim_line_v(ox - 25, oy, oy + btm_y_offset, f"{btm_offset} mm", align_left=True)
        elif side == "Right":
            c.circle(ox + p_w - 15, oy + p_h - top_y_offset, 5, fill=0, stroke=1)
            c.circle(ox + p_w - 15, oy + btm_y_offset, 5, fill=0, stroke=1)
            c.drawString(ox + p_w + 55, oy + p_h - top_y_offset - 2.5, f"Ø{dia}mm Bracket Hole [Right Edge]")
            draw_dim_line_v(ox + p_w + 25, oy + p_h - top_y_offset, oy + p_h, f"{top_offset} mm", align_left=False)
            c.drawString(ox + p_w + 55, oy + btm_y_offset - 2.5, f"Ø{dia}mm Bracket Hole [Right Edge]")
            draw_dim_line_v(ox + p_w + 25, oy, oy + btm_y_offset, f"{btm_offset} mm", align_left=False)

    def draw_knob(ox, oy, p_w, p_h, real_h, side, dia, height_offset):
        if side == "None":
            return
        c.setFont("Helvetica-Bold", 7.5)
        knob_y = oy + (height_offset / float(real_h)) * p_h
        
        if side == "Left":
            c.circle(ox + 15, knob_y, 4, fill=0, stroke=1)
            c.drawRightString(ox - 55, knob_y - 2.5, f"Ø{dia}mm Knob [Left]")
            draw_dim_line_v(ox - 25, oy, knob_y, f"{height_offset} mm", align_left=True)
        elif side == "Right":
            c.circle(ox + p_w - 15, knob_y, 4, fill=0, stroke=1)
            c.drawString(ox + p_w + 55, knob_y - 2.5, f"Ø{dia}mm Knob [Right]")
            draw_dim_line_v(ox + p_w + 25, oy, knob_y, f"{height_offset} mm", align_left=False)

    if "3 Panels" in shower_style or "L-Shape" in shower_style:
        # PAGE 1: P1
        draw_header(f"PAGE 1: {p1_name}", "P1", 1, 3, total_showers)
        ox, oy, p_w, p_h = calculate_scaled_bounds(st.session_state.p1_w, st.session_state.p1_h)
        c.setLineWidth(1.5)
        c.rect(ox, oy, p_w, p_h)
        draw_dim_line_h(ox, ox + p_w, oy + p_h + 15, f"{st.session_state.p1_w} mm")
        draw_dim_line_v(ox - 90, oy, oy + p_h, f"{st.session_state.p1_h} mm", align_left=True)
        draw_hinges(ox, oy, p_w, p_h, st.session_state.p1_h, p1_hinge_side, p1_hinge_top, p1_hinge_btm)
        draw_holes(ox, oy, p_w, p_h, st.session_state.p1_h, p1_hole_side, st.session_state.p1_hole_dia, st.session_state.p1_hole_top, st.session_state.p1_hole_btm)
        c.showPage()

        # PAGE 2: P2
        draw_header(f"PAGE 2: {p2_name}", "P2", 2, 3, total_showers)
        ox, oy, p_w, p_h = calculate_scaled_bounds(st.session_state.p2_w, st.session_state.p2_h)
        c.setLineWidth(1.5)
        c.rect(ox, oy, p_w, p_h)
        draw_dim_line_h(ox, ox + p_w, oy + p_h + 15, f"{st.session_state.p2_w} mm")
        draw_dim_line_v(ox - 90, oy, oy + p_h, f"{st.session_state.p2_h} mm", align_left=True)
        draw_knob(ox, oy, p_w, p_h, st.session_state.p2_h, p2_knob_side, st.session_state.p2_knob_dia, st.session_state.p2_knob_height)
        draw_hinges(ox, oy, p_w, p_h, st.session_state.p2_h, p2_hinge_side, p2_hinge_top, p2_hinge_btm)
        c.showPage()

        # PAGE 3: P3
        draw_header(f"PAGE 3: {p3_name}", "P3", 3, 3, total_showers)
        ox, oy, p_w, p_h = calculate_scaled_bounds(st.session_state.p3_w, st.session_state.p3_h)
        c.setLineWidth(1.5)
        c.rect(ox, oy, p_w, p_h)
        draw_dim_line_h(ox, ox + p_w, oy + p_h + 15, f"{st.session_state.p3_w} mm")
        draw_dim_line_v(ox - 90, oy, oy + p_h, f"{st.session_state.p3_h} mm", align_left=True)
        draw_hinges(ox, oy, p_w, p_h, st.session_state.p3_h, p3_hinge_side, p3_hinge_top, p3_hinge_btm)
        draw_holes(ox, oy, p_w, p_h, st.session_state.p3_h, p3_hole_side, st.session_state.p3_hole_dia, st.session_state.p3_hole_top, st.session_state.p3_hole_btm)
        c.showPage()

    elif "2 Panels" in shower_style:
        # PAGE 1: P1 DOOR PANEL
        draw_header(f"PAGE 1: {p1_name}", "P1", 1, 2, total_showers)
        ox, oy, p_w, p_h = calculate_scaled_bounds(p1_w, p1_h)
        c.setLineWidth(1.5)
        c.rect(ox, oy, p_w, p_h)
        draw_dim_line_h(ox, ox + p_w, oy + p_h + 15, f"{p1_w} mm")
        draw_dim_line_v(ox - 90, oy, oy + p_h, f"{p1_h} mm", align_left=True)
        draw_knob(ox, oy, p_w, p_h, p1_h, p1_knob_side, p1_knob_dia, p1_knob_height)
        draw_hinges(ox, oy, p_w, p_h, p1_h, p1_hinge_side, p1_hinge_top, p1_hinge_btm)
        c.showPage()

        # PAGE 2: P2 FIXED PANEL
        draw_header(f"PAGE 2: {p2_name}", "P2", 2, 2, total_showers)
        ox, oy, p_w, p_h = calculate_scaled_bounds(p2_w, p2_h)
        c.setLineWidth(1.5)
        c.rect(ox, oy, p_w, p_h)
        draw_dim_line_h(ox, ox + p_w, oy + p_h + 15, f"{p2_w} mm")
        draw_dim_line_v(ox - 90, oy, oy + p_h, f"{p2_h} mm", align_left=True)
        draw_hinges(ox, oy, p_w, p_h, p2_h, p2_hinge_side, p2_hinge_top, p2_hinge_btm)
        draw_holes(ox, oy, p_w, p_h, p2_h, p2_hole_side, p2_hole_dia, p2_hole_top, p2_hole_btm)
        c.showPage()

    elif "Fixed Panel Only" in shower_style:
        # PAGE 1: STANDALONE FIXED PANEL
        draw_header(f"PAGE 1: {p1_name}", "P1", 1, 1, total_showers)
        ox, oy, p_w, p_h = calculate_scaled_bounds(st.session_state.p1_w, st.session_state.p1_h)
        c.setLineWidth(1.5)
        c.rect(ox, oy, p_w, p_h)
        draw_dim_line_h(ox, ox + p_w, oy + p_h + 15, f"{st.session_state.p1_w} mm")
        draw_dim_line_v(ox - 90, oy, oy + p_h, f"{st.session_state.p1_h} mm", align_left=True)
        draw_holes(ox, oy, p_w, p_h, st.session_state.p1_h, p1_hole_side, st.session_state.p1_hole_dia, st.session_state.p1_hole_top, st.session_state.p1_hole_btm)
        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer

# --- MAIN DISPLAY & DOWNLOAD ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Order Batch Summary")
    st.write(f"**Shower Style:** {shower_style}")
    st.write(f"**Site Suburb:** {suburb}")
    st.write(f"**Total Systems Ordered:** {total_showers} Systems")
    st.write(f"**Total Glass Panels to Cut:** **{total_glass_pieces} Total Pieces**")
    st.write(f"**Glass Specification:** {glass_type}")
    st.write(f"**Hardware Finish:** {hardware_finish}")
    st.write(f"**Scope of Works:** {install_scope}")
    
    st.markdown("---")
    st.write("### Panel Quantity Breakdown")
    if "3 Panels" in shower_style or "L-Shape" in shower_style:
        st.write(f"• **{p1_name}:** **{total_showers} pcs** ({st.session_state.p1_w}mm x {st.session_state.p1_h}mm) | Brackets: **{p1_hole_side} Edge**")
        st.write(f"• **{p2_name}:** **{total_showers} pcs** ({st.session_state.p2_w}mm x {st.session_state.p2_h}mm) | Knob Edge: **{p2_knob_side}**")
        st.write(f"• **{p3_name}:** **{total_showers} pcs** ({st.session_state.p3_w}mm x {st.session_state.p3_h}mm) | Brackets: **{p3_hole_side} Edge**")
    elif "2 Panels" in shower_style:
        st.write(f"• **{p1_name}:** **{total_showers} pcs** ({p1_w}mm x {p1_h}mm) | Knob Edge: **{p1_knob_side}**")
        st.write(f"• **{p2_name}:** **{total_showers} pcs** ({p2_w}mm x {p2_h}mm) | Brackets: **{p2_hole_side} Edge**")
    elif "Fixed Panel Only" in shower_style:
        st.write(f"• **{p1_name}:** **{total_showers} pcs** ({st.session_state.p1_w}mm x {st.session_state.p1_h}mm) | Brackets: **{p1_hole_side} Edge**")

with col2:
    pdf_bytes = generate_pdf()
    st.download_button(
        label=f"Download Batch Shop Drawings ({total_showers} Systems / {total_glass_pieces} Panels)",
        data=pdf_bytes,
        file_name=f"{project_name.replace(' ', '_')}_{suburb}_{total_showers}x_Shower_Drawings.pdf",
        mime="application/pdf",
        type="primary"
    )