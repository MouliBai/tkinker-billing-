# Import required modules
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Image, Table, TableStyle
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.graphics.barcode import code128
from reportlab.lib import colors
from datetime import datetime

# =========================================================
# 1. CONFIGURATION
# =========================================================

WIDTH_INCH = 4   # 🔁 change to 4 for 4-inch printer
width_mm = WIDTH_INCH * 25.4

# Margins (single source of truth)
LEFT_MARGIN = 5
RIGHT_MARGIN = 5

shop_name = "Evo Aura"
shop_address = "Bazaar Street, Shoolagiri - 635117"
phone = "Phone : 9876543210"
gst = "GSTIN : 29ABCDE1234F1Z5"

# invoice details
bill_no = "Bill No.: INV18/22-23"
date = datetime.now()
date_time = "Date: " + date.strftime("%d-%m-%Y %H:%M:%S")
customer = "Harish, Mysore"

# Items
items = [
    ("Apple", 50),
    ("Banana", 30),
    ("Milk", 60),
    ("Bread", 40),
    ("Eggs", 70),
    ("Apple", 50),
    ("Banana", 30),
    ("Milk", 60),
    ("Bread", 40),
    ("Eggs", 70),
    ("Apple", 50),
    ("Banana", 30),
    ("Milk", 60),
    ("Bread", 40),
    ("Eggs", 70),
    ("Apple", 50),
    ("Banana", 30),
    ("Milk", 60),
    ("Bread", 40),
    ("Eggs", 70),
    ("Apple", 50),
    ("Banana", 30),
    ("Milk", 60),
    ("Bread", 40),
    ("Eggs", 70)
    
]

total_amount = sum(price for name, price in items)

# Styles
styles = getSampleStyleSheet()

center_style = ParagraphStyle(
    name="Center",
    parent=styles["Normal"],
    alignment=TA_CENTER
)

# =========================================================
# 2. STATIC ELEMENTS
# =========================================================

# Logo (auto fit for 3"/4")
logo = Image("logo.png")
logo._restrictSize((WIDTH_INCH - 0.5) * 72, 35 * mm)
logo.hAlign = 'CENTER'

# Text elements

shop_name_text = Paragraph(f"<b>{shop_name}</b>", center_style)
shop_address_text = Paragraph(shop_address, center_style)
phone_text = Paragraph(phone, center_style)
gst_text = Paragraph(gst, center_style)

solid_line = HRFlowable(width="100%", thickness=1)
dotted_line = HRFlowable(width="100%", thickness=1, dash=(2, 2))

footer_text = Paragraph("Thank You! Visit Again", styles["Normal"])

# Barcode
barcode = code128.Code128(bill_no, barHeight=15*mm, barWidth=0.4)
barcode.hAlign = 'CENTER'

# =========================================================
# 3. BUILD TABLE (CORRECT DYNAMIC WIDTH)
# =========================================================

# Calculate usable width (REAL FIX)
usable_width = width_mm * mm - ((LEFT_MARGIN + RIGHT_MARGIN) * mm)

# Column ratios
if WIDTH_INCH == 3:
    ratios = [0.5, 0.2, 0.3]
else:
    ratios = [0.6, 0.15, 0.25]

col_widths = [usable_width * r for r in ratios]

# Table data
table_data = [["Item","Qty", "Amt"]]

for i, (name, price) in enumerate(items, start=1):
    table_data.append([f"{i}. {name}", "1", f"{price:.2f}"])

# Create table
table = Table(table_data, colWidths=col_widths)

# Style
table.setStyle(TableStyle([
    ("FONT", (0,0), (-1,-1), "Helvetica"),
    ("FONTSIZE", (0,0), (-1,-1), 8),

    ("ALIGN", (0,0), (0,-1), "LEFT"),     # Item
    ("ALIGN", (1,0), (1,-1), "CENTER"),   # Qty
    ("ALIGN", (2,0), (2,-1), "RIGHT"),    # Amount

    ("LINEBELOW", (0,0), (-1,0), 1, colors.black),

    ("LEFTPADDING", (0,0), (-1,-1), 2),
    ("RIGHTPADDING", (0,0), (-1,-1), 2),
    ("BOTTOMPADDING", (0,0), (-1,0), 6),
]))

# =========================================================
# 4. BUILD CONTENT
# =========================================================

content = []

content.append(logo)
content.append(shop_name_text)
content.append(shop_address_text)
content.append(phone_text)
content.append(gst_text)

content.append(solid_line)
content.append(Paragraph("<b>Tax Invoice / Receipt</b>", center_style))
content.append(solid_line)
content.append(Paragraph(bill_no))
content.append(Paragraph(date_time))

content.append(solid_line)
content.append(Spacer(1, 4))

content.append(table)

content.append(Spacer(1, 4))
content.append(solid_line)
content.append(Paragraph(f"Total: Rs {total_amount:.2f}", styles["Normal"]))

content.append(dotted_line)
content.append(Spacer(1, 6))
content.append(footer_text)

# Barcode
content.append(Spacer(1, 8))
content.append(barcode)
content.append(Paragraph(bill_no, center_style))

# =========================================================
# 5. DYNAMIC HEIGHT
# =========================================================

def calculate_height(content, width):
    total_height = 0
    for flowable in content:
        w, h = flowable.wrap(width, 1000)
        total_height += h
    return total_height

# Pre-wrap
for flowable in content:
    flowable.wrapOn(None, width_mm * mm, 1000)

calculated_height = calculate_height(content, width_mm * mm)

# Safe buffer
final_height = calculated_height + 30

# =========================================================
# 6. CREATE PDF
# =========================================================

doc = SimpleDocTemplate(
    "receipt.pdf",
    pagesize=(width_mm * mm, final_height),
    leftMargin=LEFT_MARGIN,
    rightMargin=RIGHT_MARGIN,
    topMargin=5,
    bottomMargin=0
)

doc.build(content)