import streamlit as st
import io
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors

st.set_page_config(page_title="SSG Shop Drawing Generator", layout="wide")

st.title("Shower Screens & Glass (SSG) - Shop Drawing Generator")
st.write("Parametric CAD shop drawing tool with proportionally scaled glass panels and dimension lines.")

# --- STEP 1: SHOWER STYLE SELECTION ---
st.sidebar.header("1. Shower Screen Style")
shower_style = st.sidebar.selectbox(
    "Select Shower Screen Layout",
    options=[
        "L-Shape (3 Panels: Return, Door, Fixed)",
        "Fixed Panel Only (1 Panel)",
        "Style 3 (To Be Specified)"
    ],
    index=0
)

# --- STEP 2: BATCH JOB QUANTITY ---
st.sidebar.header("2. Job Order Quantity")
total_showers = st.sidebar.number_input("Total Number of Showers (Systems)", min_value=1, value=5, step=1)

# --- STEP 3: JOB HEADER DETAILS ---
st.sidebar.header("3. Job & Header Details")
project_name = st.sidebar.text_input("Project Name", value="Castle Hill")
date_str = st.sidebar.text_input("Date", value="22/09/2026")
supplier = st.sidebar.text_input("Supplier", value="Standard Supplier")
glass_type = st.sidebar.text_input("Glass Spec", value="10mm MetaLUX Toughened")

# --- STEP 4: GLOBAL HINGE SPECS ---
st.sidebar.header("4. Global Hinge Model Specs")
hinge_type = st.sidebar.text_input("Hinge Model Name", value="SUL Hinge")
hinge_w = st.sidebar.number_input("Hinge Cutout Width (mm)", value=65)
hinge_h = st.sidebar.number_input("Hinge Cutout Height (mm)", value=44)
hinge_r = st.sidebar.number_input("Corner Radius r (mm)", value=8)

# --- STEP 5: PANEL CONFIGURATIONS ---
if "L-Shape" in shower_style:
    st.sidebar.header("5. Panel 1 (Return Panel)")
    p1_w = st.sidebar.number_input("P1 Width (mm)", value=1200)
    p1_h = st.sidebar.number_input("P1 Height (mm)", value=2400)
    p1_hinge_side = st.sidebar.selectbox("P1 Hinge Edge", options=["Left", "Right", "None"], index=0)
    p1_hinge_top = st.sidebar.number_input("P1 Hinge Top Offset (mm)", value=200, key="p1_ht")
    p1_hinge_btm = st.sidebar.number_input("P1 Hinge Bottom Offset (mm)", value=200, key="p1_hb")
    p1_hole_side = st.sidebar.selectbox("P1 Bracket Hole Edge", options=["Right", "Left", "None"], index=0)
    p1_hole_dia = st.sidebar.number_input("P1 Bracket Hole Diameter (mm)", value=22)
    p1_hole_offset = st.sidebar.number_input("P1 Bracket Hole Offset (mm)", value=200)

    st.sidebar.header("6. Panel 2 (Door Panel)")
    p2_w = st.sidebar.number_input("P2 Width (mm)", value=800)
    p2_h = st.sidebar.number_input("P2 Height (mm)", value=2100)
    p2_hinge_side = st.sidebar.selectbox("P2 Hinge Edge", options=["Right", "Left", "None"], index=0)
    p2_hinge_top = st.sidebar.number_input("P2 Hinge Top Offset (mm)", value=200, key="p2_ht")
    p2_hinge_btm = st.sidebar.number_input("P2 Hinge Bottom Offset (mm)", value=200, key="p2_hb")
    p2_knob_dia = st.sidebar.number_input("P2 Pull Knob Hole Diameter (mm)", value=12)
    p2_knob_height = st.sidebar.number_input("P2 Knob Height From Bottom (mm)", value=1050)

    st.sidebar.header("7. Panel 3 (Right Fixed Panel)")
    p3_w = st.sidebar.number_input("P3 Width (mm)", value=760)
    p3_h = st.sidebar.number_input("P3 Height (mm)", value=2400)
    p3_hinge_side = st.sidebar.selectbox("P3 Hinge Edge", options=["None", "Left", "Right"], index=0)
    p3_hinge_top = st.sidebar.number_input("P3 Hinge Top Offset (mm)", value=200, key="p3_ht")
    p3_hinge_btm = st.sidebar.number_input("P3 Hinge Bottom Offset (mm)", value=200, key="p3_hb")
    p3_hole_side = st.sidebar.selectbox("P3 Bracket Hole Edge", options=["Left", "Right", "None"], index=0)
    p3_hole_dia = st.sidebar.number_input("P3 Bracket Hole Diameter (mm)", value=22)
    p3_hole_offset = st.sidebar.number_input("P3 Bracket Hole Offset (mm)", value=200)

elif "Fixed Panel Only" in shower_style:
    st.sidebar.header("5. Fixed Panel Specs")
    p1_w = st.sidebar.number_input("Fixed Panel Width (mm)", value=900)
    p1_h = st.sidebar.number_input("Fixed Panel Height (mm)", value=2000)
    p1_hole_side = st.sidebar.selectbox("Bracket Hole Edge", options=["Left", "Right", "None"], index=0)
    p1_hole_dia = st.sidebar.number_input("Bracket Hole Diameter (mm)", value=22)
    p1_hole_offset = st.sidebar.number_input("Bracket Hole Offset (mm)", value=200)

# --- PDF GENERATION ENGINE ---
def generate_pdf():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(letter))
    page_w, page_h = landscape(letter)

    def calculate_scaled_bounds(real_w, real_h):
        """Calculates canvas pixel dimensions proportional to real aspect ratio."""
        max_draw_w = 280.0
        max_draw_h = 320.0
        
        aspect = real_w / float(real_h)
        
        if (max_draw_w / aspect) <= max_draw_h:
            p_w = max_draw_w
            p_h = max_draw_w / aspect
        else:
            p_h = max_draw_h
            p_w = max_draw_h * aspect
            
        ox = (page_w - p_w) / 2
        oy = (page_h - p_h) / 2 - 20
        return ox, oy, p_w, p_h

    def draw_header(title, mark_id, qty):
        c.setLineWidth(1)
        c.setStrokeColor(colors.black)
        c.rect(30, 30, page_w - 60, page_h - 60)
        
        tb_y = page_h - 90
        c.rect(40, tb_y, page_w - 80, 50)
        
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, tb_y + 30, "SHOWER SCREENS & GLASS (SSG)")
        
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(page_w - 50, tb_y + 30, f"PROJECT: {project_name.upper()}")
        
        c.setFont("Helvetica", 9)
        c.drawString(50, tb_y + 10, f"Mark: {mark_id}  |  TOTAL QTY REQUIRED: {qty} PCS  |  Supplier: {supplier}  |  Glass: {glass_type}")
        c.drawRightString(page_w - 50, tb_y + 10, f"Date: {date_str}  |  Edgework: FP 4 Sides  |  Stamp: No Stamp")
        
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, page_h - 110, title)

    def draw_dim_line_h(x1, x2, y, label):
        c.setLineWidth(0.6)
        c.line(x1, y - 5, x1, y + 5)
        c.line(x2, y - 5, x2, y + 5)
        c.line(x1, y, x2, y)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString((x1 + x2) / 2, y + 4, label)

    def draw_dim_line_v(x, y1, y2, label):
        c.setLineWidth(0.6)
        c.line(x - 5, y1, x + 5, y1)
        c.line(x - 5, y2, x + 5, y2)
        c.line(x, y1, x, y2)
        c.setFont("Helvetica-Bold", 9)
        c.drawRightString(x - 8, (y1 + y2) / 2 - 3, label)

    def draw_hinges(ox, oy, p_w, p_h, real_h, side, top_offset, btm_offset):
        if side == "None":
            return
        c.setFont("Helvetica", 7)
        top_y_offset = (top_offset / float(real_h)) * p_h
        btm_y_offset = (btm_offset / float(real_h)) * p_h

        if side == "Left":
            # Top Notch
            c.rect(ox, oy + p_h - top_y_offset - 9, 12, 18, fill=1, stroke=1)
            c.drawRightString(ox - 35, oy + p_h - top_y_offset + 3, f"{hinge_type} ({hinge_w}x{hinge_h}mm, r={hinge_r}mm)")
            draw_dim_line_v(ox - 20, oy + p_h - top_y_offset, oy + p_h, f"{top_offset} mm")
            # Bottom Notch
            c.rect(ox, oy + btm_y_offset - 9, 12, 18, fill=1, stroke=1)
            c.drawRightString(ox - 35, oy + btm_y_offset + 3, f"{hinge_type} ({hinge_w}x{hinge_h}mm, r={hinge_r}mm)")
            draw_dim_line_v(ox - 20, oy, oy + btm_y_offset, f"{btm_offset} mm")
        elif side == "Right":
            # Top Notch
            c.rect(ox + p_w - 12, oy + p_h - top_y_offset - 9, 12, 18, fill=1, stroke=1)
            c.drawString(ox + p_w + 35, oy + p_h - top_y_offset + 3, f"{hinge_type} ({hinge_w}x{hinge_h}mm, r={hinge_r}mm)")
            draw_dim_line_v(ox + p_w + 20, oy + p_h - top_y_offset, oy + p_h, f"{top_offset} mm")
            # Bottom Notch
            c.rect(ox + p_w - 12, oy + btm_y_offset - 9, 12, 18, fill=1, stroke=1)
            c.drawString(ox + p_w + 35, oy + btm_y_offset + 3, f"{hinge_type} ({hinge_w}x{hinge_h}mm, r={hinge_r}mm)")
            draw_dim_line_v(ox + p_w + 20, oy, oy + btm_y_offset, f"{btm_offset} mm")

    def draw_holes(ox, oy, p_w, p_h, real_h, side, dia, offset):
        if side == "None":
            return
        c.setFont("Helvetica", 7)
        top_y_offset = (offset / float(real_h)) * p_h
        btm_y_offset = (offset / float(real_h)) * p_h

        if side == "Left":
            c.circle(ox + 15, oy + p_h - top_y_offset, 5, fill=0, stroke=1)
            c.circle(ox + 15, oy + btm_y_offset, 5, fill=0, stroke=1)
            c.drawRightString(ox - 35, oy + p_h - top_y_offset - 3, f"Ø{dia}mm Bracket Hole")
            draw_dim_line_v(ox - 20, oy + p_h - top_y_offset, oy + p_h, f"{offset} mm")
            c.drawRightString(ox - 35, oy + btm_y_offset - 3, f"Ø{dia}mm Bracket Hole")
            draw_dim_line_v(ox - 20, oy, oy + btm_y_offset, f"{offset} mm")
        elif side == "Right":
            c.circle(ox + p_w - 15, oy + p_h - top_y_offset, 5, fill=0, stroke=1)
            c.circle(ox + p_w - 15, oy + btm_y_offset, 5, fill=0, stroke=1)
            c.drawString(ox + p_w + 35, oy + p_h - top_y_offset - 3, f"Ø{dia}mm Bracket Hole")
            draw_dim_line_v(ox + p_w + 20, oy + p_h - top_y_offset, oy + p_h, f"{offset} mm")
            c.drawString(ox + p_w + 35, oy + btm_y_offset - 3, f"Ø{dia}mm Bracket Hole")
            draw_dim_line_v(ox + p_w + 20, oy, oy + btm_y_offset, f"{offset} mm")

    if "L-Shape" in shower_style:
        # PAGE 1: P1
        draw_header("PAGE 1: P1 — L-SHAPE RETURN PANEL", "P1", total_showers)
        ox, oy, p_w, p_h = calculate_scaled_bounds(p1_w, p1_h)
        c.setLineWidth(1.5)
        c.rect(ox, oy, p_w, p_h)
        draw_dim_line_h(ox, ox + p_w, oy + p_h + 15, f"{p1_w} mm")
        draw_dim_line_v(ox - 60, oy, oy + p_h, f"{p1_h} mm")
        draw_hinges(ox, oy, p_w, p_h, p1_h, p1_hinge_side, p1_hinge_top, p1_hinge_btm)
        draw_holes(ox, oy, p_w, p_h, p1_h, p1_hole_side, p1_hole_dia, p1_hole_offset)
        c.showPage()

        # PAGE 2: P2
        draw_header("PAGE 2: P2 — DOOR PANEL", "P2", total_showers)
        ox, oy, p_w, p_h = calculate_scaled_bounds(p2_w, p2_h)
        c.setLineWidth(1.5)
        c.rect(ox, oy, p_w, p_h)
        draw_dim_line_h(ox, ox + p_w, oy + p_h + 15, f"{p2_w} mm")
        draw_dim_line_v(ox - 60, oy, oy + p_h, f"{p2_h} mm")
        knob_y = oy + (p2_knob_height / float(p2_h)) * p_h
        c.circle(ox + 15, knob_y, 4, fill=0, stroke=1)
        c.setFont("Helvetica", 7)
        c.drawRightString(ox - 35, knob_y - 3, f"Ø{p2_knob_dia}mm Knob")
        draw_dim_line_v(ox - 20, oy, knob_y, f"{p2_knob_height} mm")
        draw_hinges(ox, oy, p_w, p_h, p2_h, p2_hinge_side, p2_hinge_top, p2_hinge_btm)
        c.showPage()

        # PAGE 3: P3
        draw_header("PAGE 3: P3 — RIGHT FIXED PANEL", "P3", total_showers)
        ox, oy, p_w, p_h = calculate_scaled_bounds(p3_w, p3_h)
        c.setLineWidth(1.5)
        c.rect(ox, oy, p_w, p_h)
        draw_dim_line_h(ox, ox + p_w, oy + p_h + 15, f"{p3_w} mm")
        draw_dim_line_v(ox - 60, oy, oy + p_h, f"{p3_h} mm")
        draw_hinges(ox, oy, p_w, p_h, p3_h, p3_hinge_side, p3_hinge_top, p3_hinge_btm)
        draw_holes(ox, oy, p_w, p_h, p3_h, p3_hole_side, p3_hole_dia, p3_hole_offset)
        if p3_hinge_side != "Right" and p3_hole_side != "Right":
            c.setFont("Helvetica", 8)
            c.drawString(ox + p_w + 15, oy + p_h/2, "(Clean Straight Edge)")
        c.showPage()

    elif "Fixed Panel Only" in shower_style:
        # PAGE 1: STANDALONE FIXED PANEL
        draw_header("PAGE 1: P1 — STANDALONE FIXED PANEL", "P1", total_showers)
        ox, oy, p_w, p_h = calculate_scaled_bounds(p1_w, p1_h)
        c.setLineWidth(1.5)
        c.rect(ox, oy, p_w, p_h)
        draw_dim_line_h(ox, ox + p_w, oy + p_h + 15, f"{p1_w} mm")
        draw_dim_line_v(ox - 60, oy, oy + p_h, f"{p1_h} mm")
        draw_holes(ox, oy, p_w, p_h, p1_h, p1_hole_side, p1_hole_dia, p1_hole_offset)
        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer

# --- MAIN DISPLAY & DOWNLOAD ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Order Batch Summary")
    st.write(f"**Shower Style:** {shower_style}")
    st.write(f"**Total Showers Ordered:** {total_showers} Systems")
    if "L-Shape" in shower_style:
        st.write(f"• **P1 Return Panels Needed:** {total_showers} pcs ({p1_w}mm x {p1_h}mm)")
        st.write(f"• **P2 Door Panels Needed:** {total_showers} pcs ({p2_w}mm x {p2_h}mm)")
        st.write(f"• **P3 Fixed Panels Needed:** {total_showers} pcs ({p3_w}mm x {p3_h}mm)")
    elif "Fixed Panel Only" in shower_style:
        st.write(f"• **Standalone Fixed Panels Needed:** {total_showers} pcs ({p1_w}mm x {p1_h}mm)")

with col2:
    if "Style 3" not in shower_style:
        pdf_bytes = generate_pdf()
        st.download_button(
            label=f"Download Batch Shop Drawings ({total_showers} Systems)",
            data=pdf_bytes,
            file_name=f"{project_name.replace(' ', '_')}_{total_showers}x_Shower_Drawings.pdf",
            mime="application/pdf",
            type="primary"
        )
    else:
        st.info("Please specify Style 3 parameters to generate shop drawings.")