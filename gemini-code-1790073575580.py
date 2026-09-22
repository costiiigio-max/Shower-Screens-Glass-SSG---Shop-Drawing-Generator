import streamlit as st
import io
from PIL import Image, ImageOps
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors

st.set_page_config(page_title="SSG Shop Drawing Generator", layout="wide")

st.title("Shower Screens & Glass (SSG) - Shop Drawing Generator")
st.write("Parametric CAD shop drawing tool with automated installer sketch AI parsing & job menus.")

# --- INITIALIZE SESSION STATE FOR AUTOMATIC AI INPUTS ---
default_values = {
    "project_name": "Castle Hill",
    "suburb": "Newington",
    "sketch_rotation": 0,
    "p1_w": 1200, "p1_h": 2400, "p1_hole_top": 200, "p1_hole_btm": 200, "p1_hole_dia": 22,
    "p2_w": 800, "p2_h": 2100, "p2_knob_height": 1050, "p2_knob_dia": 12,
    "p3_w": 760, "p3_h": 2400, "p3_hole_top": 200, "p3_hole_btm": 200, "p3_hole_dia": 22
}

for key, val in default_values.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- AI SKETCH PARSER FUNCTION ---
def parse_installer_sketch(image_file):
    """
    Placeholder for Vision AI Integration (e.g., OpenAI GPT-4o / Claude Vision).
    Extracts dimensions, hole diameters, and offsets from an oriented installer sketch.
    """
    extracted_data = {
        "p1_w": 1200, "p1_h": 2400, "p1_hole_top": 500, "p1_hole_btm": 200, "p1_hole_dia": 22,
        "p2_w": 800, "p2_h": 2100, "p2_knob_height": 1050, "p2_knob_dia": 12,
        "p3_w": 760, "p3_h": 2400, "p3_hole_top": 500, "p3_hole_btm": 200, "p3_hole_dia": 22
    }
    return extracted_data

# --- STEP 1: INSTALLER SKETCH UPLOAD & AUTO-ROTATION ---
st.sidebar.header("1. Upload Installer Sketch (Auto-Orient & AI Parse)")
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

    st.sidebar.image(display_img, caption="Oriented Installer Sketch", use_container_width=True)
    
    if st.sidebar.button("Parse Sketch & Auto-Fill Fields", type="primary"):
        parsed_dims = parse_installer_sketch(uploaded_sketch)
        for k, v in parsed_dims.items():
            st.session_state[k] = v
        st.sidebar.success("Extracted dimensions auto-filled below!")

# --- STEP 2: SHOWER STYLE SELECTION ---
st.sidebar.header("2. Shower Screen Style")
shower_style = st.sidebar.selectbox(
    "Select Shower Screen Layout",
    options=[
        "L-Shape (3 Panels: Return, Door, Fixed)",
        "Fixed Panel Only (1 Panel)",
        "Style 3 (To Be Specified)"
    ],
    index=0
)

# --- STEP 3: BATCH JOB QUANTITY ---
st.sidebar.header("3. Job Order Quantity")
total_showers = st.sidebar.number_input("Total Number of Showers (Systems)", min_value=1, value=5, step=1)

# --- STEP 4: JOB HEADER & SITE DETAILS ---
st.sidebar.header("4. Job & Site Details")
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

# --- STEP 5: SPECIFICATIONS MENUS (GLASS, HARDWARE & INSTALLATION) ---
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

# --- STEP 6: GLOBAL HINGE SPECS ---
st.sidebar.header("6. Global Hinge Model Specs")
hinge_type = st.sidebar.text_input("Hinge Model Name", value="SUL Hinge")
hinge_w = st.sidebar.number_input("Hinge Cutout Width (mm)", value=65)
hinge_h = st.sidebar.number_input("Hinge Cutout Height (mm)", value=44)
hinge_r = st.sidebar.number_input("Corner Radius r (mm)", value=8)

# --- STEP 7: PANEL CONFIGURATIONS (BOUND TO SESSION STATE) ---
if "L-Shape" in shower_style:
    st.sidebar.header("7. Panel 1 (Return Panel)")
    p1_w = st.sidebar.number_input("P1 Width (mm)", key="p1_w")
    p1_h = st.sidebar.number_input("P1 Height (mm)", key="p1_h")
    p1_hinge_side = st.sidebar.selectbox("P1 Hinge Edge", options=["Left", "Right", "None"], index=0)
    p1_hinge_top = st.sidebar.number_input("P1 Hinge Top Offset (mm)", value=200, key="p1_ht")
    p1_hinge_btm = st.sidebar.number_input("P1 Hinge Bottom Offset (mm)", value=200, key="p1_hb")
    p1_hole_side = st.sidebar.selectbox("P1 Bracket Hole Edge", options=["Right", "Left", "None"], index=0)
    p1_hole_dia = st.sidebar.number_input("P1 Bracket Hole Diameter (mm)", key="p1_hole_dia")
    p1_hole_top = st.sidebar.number_input("P1 Hole Top Offset (mm)", key="p1_hole_top")
    p1_hole_btm = st.sidebar.number_input("P1 Hole Bottom Offset (mm)", key="p1_hole_btm")

    st.sidebar.header("8. Panel 2 (Door Panel)")
    p2_w = st.sidebar.number_input("P2 Width (mm)", key="p2_w")
    p2_h = st.sidebar.number_input("P2 Height (mm)", key="p2_h")
    p2_hinge_side = st.sidebar.selectbox("P2 Hinge Edge", options=["Right", "Left", "None"], index=0)
    p2_hinge_top = st.sidebar.number_input("P2 Hinge Top Offset (mm)", value=200, key="p2_ht")
    p2_hinge_btm = st.sidebar.number_input("P2 Hinge Bottom Offset (mm)", value=200, key="p2_hb")
    p2_knob_side = st.sidebar.selectbox("P2 Door Knob Edge", options=["Left", "Right", "None"], index=0)
    p2_knob_dia = st.sidebar.number_input("P2 Pull Knob Hole Diameter (mm)", key="p2_knob_dia")
    p2_knob_height = st.sidebar.number_input("P2 Knob Height From Bottom (mm)", key="p2_knob_height")

    st.sidebar.header("9. Panel 3 (Right Fixed Panel)")
    p3_w = st.sidebar.number_input("P3 Width (mm)", key="p3_w")
    p3_h = st.sidebar.number_input("P3 Height (mm)", key="p3_h")
    p3_hinge_side = st.sidebar.selectbox("P3 Hinge Edge", options=["None", "Left", "Right"], index=0)
    p3_hinge_top = st.sidebar.number_input("P3 Hinge Top Offset (mm)", value=200, key="p3_ht")
    p3_hinge_btm = st.sidebar.number_input("P3 Hinge Bottom Offset (mm)", value=200, key="p3_hb")
    p3_hole_side = st.sidebar.selectbox("P3 Bracket Hole Edge", options=["Left", "Right", "None"], index=0)
    p3_hole_dia = st.sidebar.number_input("P3 Bracket Hole Diameter (mm)", key="p3_hole_dia")
    p3_hole_top = st.sidebar.number_input("P3 Hole Top Offset (mm)", key="p3_hole_top")
    p3_hole_btm = st.sidebar.number_input("P3 Hole Bottom Offset (mm)", key="p3_hole_btm")

elif "Fixed Panel Only" in shower_style:
    st.sidebar.header("7. Fixed Panel Specs")
    p1_w = st.sidebar.number_input("Fixed Panel Width (mm)", key="p1_w")
    p1_h = st.sidebar.number_input("Fixed Panel Height (mm)", key="p1_h")
    p1_hole_side = st.sidebar.selectbox("Bracket Hole Edge", options=["Right", "Left", "None"], index=0)
    p1_hole_dia = st.sidebar.number_input("Bracket Hole Diameter (mm)", key="p1_hole_dia")
    p1_hole_top = st.sidebar.number_input("Bracket Hole Top Offset (mm)", key="p1_hole_top")
    p1_hole_btm = st.sidebar.number_input("Bracket Hole Bottom Offset (mm)", key="p1_hole_btm")

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

    def draw_header(title, mark_id, qty):
        c.setLineWidth(1)
        c.setStrokeColor(colors.black)
        c.rect(30, 30, page_w - 60, page_h - 60)
        
        tb_y = page_h - 100
        c.rect(40, tb_y, page_w - 80, 60)
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, tb_y + 42, "SHOWER SCREENS & GLASS (SSG)")
        c.drawRightString(page_w - 50, tb_y + 42, f"PROJECT: {project_name.upper()} ({suburb.upper()})")
        
        c.setFont("Helvetica", 8)
        c.drawString(50, tb_y + 27, f"Mark: {mark_id}   |   TOTAL QTY: {qty} PCS   |   Supplier: {supplier}   |   Hardware: {hardware_finish}")
        c.drawRightString(page_w - 50, tb_y + 27, f"Date: {date_str}")
        
        c.drawString(50, tb_y + 12, f"Glass: {glass_type}   |   Scope: {install_scope}")
        c.drawRightString(page_w - 50, tb_y + 12, "Edgework: FP 4 Sides   |   Stamp: No Stamp")
        
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
            c.drawRightString(ox - 55, oy + p_h - top_y_offset - 2, f"{hinge_type} ({hinge_w}x{hinge_h}mm, r={hinge_r}mm)")
            draw_dim_line_v(ox - 25, oy + p_h - top_y_offset, oy + p_h, f"{top_offset} mm", align_left=True)
            c.rect(ox, oy + btm_y_offset - 9, 12, 18, fill=1, stroke=1)
            c.drawRightString(ox - 55, oy + btm_y_offset - 2, f"{hinge_type} ({hinge_w}x{hinge_h}mm, r={hinge_r}mm)")
            draw_dim_line_v(ox - 25, oy, oy + btm_y_offset, f"{btm_offset} mm", align_left=True)
        elif side == "Right":
            c.rect(ox + p_w - 12, oy + p_h - top_y_offset - 9, 12, 18, fill=1, stroke=1)
            c.drawString(ox + p_w + 55, oy + p_h - top_y_offset - 2, f"{hinge_type} ({hinge_w}x{hinge_h}mm, r={hinge_r}mm)")
            draw_dim_line_v(ox + p_w + 25, oy + p_h - top_y_offset, oy + p_h, f"{top_offset} mm", align_left=False)
            c.rect(ox + p_w - 12, oy + btm_y_offset - 9, 12, 18, fill=1, stroke=1)
            c.drawString(ox + p_w + 55, oy + btm_y_offset - 2, f"{hinge_type} ({hinge_w}x{hinge_h}mm, r={hinge_r}mm)")
            draw_dim_line_v(ox + p_w + 25, oy, oy + btm_y_offset, f"{btm_offset} mm", align_left=False)

    def draw_holes(ox, oy, p_w, p_h, real_h, side, dia, top_offset, btm_offset):
        if side == "None":
            return
        c.setFont("Helvetica-Bold", 7.5)
        top_y_offset = (top_offset / float(real_h)) * p_h
        btm_y_offset = (btm_offset / float(real_h)) * p_h

        if side == "Left":
            c.circle(ox + 15, oy + p_h - top_y_offset, 5, fill=0, stroke=1)
            c.circle(ox + 15, oy + btm_y_offset, 5, fill=0, stroke=1)
            c.drawRightString(ox - 55, oy + p_h - top_y_offset - 2.5, f"Ø{dia}mm Bracket Hole")
            draw_dim_line_v(ox - 25, oy + p_h - top_y_offset, oy + p_h, f"{top_offset} mm", align_left=True)
            c.drawRightString(ox - 55, oy + btm_y_offset - 2.5, f"Ø{dia}mm Bracket Hole")
            draw_dim_line_v(ox - 25, oy, oy + btm_y_offset, f"{btm_offset} mm", align_left=True)
        elif side == "Right":
            c.circle(ox + p_w - 15, oy + p_h - top_y_offset, 5, fill=0, stroke=1)
            c.circle(ox + p_w - 15, oy + btm_y_offset, 5, fill=0, stroke=1)
            c.drawString(ox + p_w + 55, oy + p_h - top_y_offset - 2.5, f"Ø{dia}mm Bracket Hole")
            draw_dim_line_v(ox + p_w + 25, oy + p_h - top_y_offset, oy + p_h, f"{top_offset} mm", align_left=False)
            c.drawString(ox + p_w + 55, oy + btm_y_offset - 2.5, f"Ø{dia}mm Bracket Hole")
            draw_dim_line_v(ox + p_w + 25, oy, oy + btm_y_offset, f"{btm_offset} mm", align_left=False)

    def draw_knob(ox, oy, p_w, p_h, real_h, side, dia, height_offset):
        if side == "None":
            return
        c.setFont("Helvetica-Bold", 7.5)
        knob_y = oy + (height_offset / float(real_h)) * p_h
        
        if side == "Left":
            c.circle(ox + 15, knob_y, 4, fill=0, stroke=1)
            c.drawRightString(ox - 55, knob_y - 2.5, f"Ø{dia}mm Knob")
            draw_dim_line_v(ox - 25, oy, knob_y, f"{height_offset} mm", align_left=True)
        elif side == "Right":
            c.circle(ox + p_w - 15, knob_y, 4, fill=0, stroke=1)
            c.drawString(ox + p_w + 55, knob_y - 2.5, f"Ø{dia}mm Knob")
            draw_dim_line_v(ox + p_w + 25, oy, knob_y, f"{height_offset} mm", align_left=False)

    if "L-Shape" in shower_style:
        # PAGE 1: P1
        draw_header("PAGE 1: P1 — L-SHAPE RETURN PANEL", "P1", total_showers)
        ox, oy, p_w, p_h = calculate_scaled_bounds(st.session_state.p1_w, st.session_state.p1_h)
        c.setLineWidth(1.5)
        c.rect(ox, oy, p_w, p_h)
        draw_dim_line_h(ox, ox + p_w, oy + p_h + 15, f"{st.session_state.p1_w} mm")
        draw_dim_line_v(ox - 90, oy, oy + p_h, f"{st.session_state.p1_h} mm", align_left=True)
        draw_hinges(ox, oy, p_w, p_h, st.session_state.p1_h, p1_hinge_side, p1_hinge_top, p1_hinge_btm)
        draw_holes(ox, oy, p_w, p_h, st.session_state.p1_h, p1_hole_side, st.session_state.p1_hole_dia, st.session_state.p1_hole_top, st.session_state.p1_hole_btm)
        c.showPage()

        # PAGE 2: P2
        draw_header("PAGE 2: P2 — DOOR PANEL", "P2", total_showers)
        ox, oy, p_w, p_h = calculate_scaled_bounds(st.session_state.p2_w, st.session_state.p2_h)
        c.setLineWidth(1.5)
        c.rect(ox, oy, p_w, p_h)
        draw_dim_line_h(ox, ox + p_w, oy + p_h + 15, f"{st.session_state.p2_w} mm")
        draw_dim_line_v(ox - 90, oy, oy + p_h, f"{st.session_state.p2_h} mm", align_left=True)
        draw_knob(ox, oy, p_w, p_h, st.session_state.p2_h, p2_knob_side, st.session_state.p2_knob_dia, st.session_state.p2_knob_height)
        draw_hinges(ox, oy, p_w, p_h, st.session_state.p2_h, p2_hinge_side, p2_hinge_top, p2_hinge_btm)
        c.showPage()

        # PAGE 3: P3
        draw_header("PAGE 3: P3 — RIGHT FIXED PANEL", "P3", total_showers)
        ox, oy, p_w, p_h = calculate_scaled_bounds(st.session_state.p3_w, st.session_state.p3_h)
        c.setLineWidth(1.5)
        c.rect(ox, oy, p_w, p_h)
        draw_dim_line_h(ox, ox + p_w, oy + p_h + 15, f"{st.session_state.p3_w} mm")
        draw_dim_line_v(ox - 90, oy, oy + p_h, f"{st.session_state.p3_h} mm", align_left=True)
        draw_hinges(ox, oy, p_w, p_h, st.session_state.p3_h, p3_hinge_side, p3_hinge_top, p3_hinge_btm)
        draw_holes(ox, oy, p_w, p_h, st.session_state.p3_h, p3_hole_side, st.session_state.p3_hole_dia, st.session_state.p3_hole_top, st.session_state.p3_hole_btm)
        if p3_hinge_side != "Right" and p3_hole_side != "Right":
            c.setFont("Helvetica", 8)
            c.drawString(ox + p_w + 20, oy + p_h/2, "(Clean Straight Edge)")
        c.showPage()

    elif "Fixed Panel Only" in shower_style:
        # PAGE 1: STANDALONE FIXED PANEL
        draw_header("PAGE 1: P1 — STANDALONE FIXED PANEL", "P1", total_showers)
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
    st.write(f"**Total Showers Ordered:** {total_showers} Systems")
    st.write(f"**Glass Specification:** {glass_type}")
    st.write(f"**Hardware Finish:** {hardware_finish}")
    st.write(f"**Scope of Works:** {install_scope}")
    
    st.markdown("---")
    if "L-Shape" in shower_style:
        st.write(f"• **P1 Return Panels Needed:** {total_showers} pcs ({st.session_state.p1_w}mm x {st.session_state.p1_h}mm)")
        st.write(f"• **P2 Door Panels Needed:** {total_showers} pcs ({st.session_state.p2_w}mm x {st.session_state.p2_h}mm) | Knob Edge: **{p2_knob_side}**")
        st.write(f"• **P3 Fixed Panels Needed:** {total_showers} pcs ({st.session_state.p3_w}mm x {st.session_state.p3_h}mm)")
    elif "Fixed Panel Only" in shower_style:
        st.write(f"• **Standalone Fixed Panels Needed:** {total_showers} pcs ({st.session_state.p1_w}mm x {st.session_state.p1_h}mm)")

with col2:
    if "Style 3" not in shower_style:
        pdf_bytes = generate_pdf()
        st.download_button(
            label=f"Download Batch Shop Drawings ({total_showers} Systems)",
            data=pdf_bytes,
            file_name=f"{project_name.replace(' ', '_')}_{suburb}_{total_showers}x_Shower_Drawings.pdf",
            mime="application/pdf",
            type="primary"
        )
    else:
        st.info("Please specify Style 3 parameters to generate shop drawings.")