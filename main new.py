# Import required modules
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Image, Table, TableStyle
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.graphics.barcode import code128
from reportlab.lib import colors
from datetime import datetime

# =========================================================
# 1. CONFIGURATION
# =========================================================

WIDTH_INCH = 4
width_mm = WIDTH_INCH * 25.4

LEFT_MARGIN = 5
RIGHT_MARGIN = 5

shop_name = "Evo Aura"
shop_address = "Bazaar Street, Shoolagiri - 635117"
phone = "Phone : 9876543210"
gst = "GSTIN : 29ABCDE1234F1Z5"

bill_no = "Bill No.: INV18/22-23"
date = datetime.now()
date_time = "Date: " + date.strftime("%d-%m-%Y %H:%M:%S")

# =========================================================
# 2. ITEMS
# =========================================================

items = [
    ("AppleAppleAppleAppleAppleAppleAppleApple", 50, 2, False, 0, 0),
    ("BananaBananaBananaBananaBananaBananaBananaBananaBananaBananaBananaBananaBanana", 30, 1, False, 0, 0),
    ("Shirt Piece", 200, 1, True, 2.5, 20),
    ("Milk", 60, 1, False, 0, 0),
    ("Bread", 40, 2, False, 0, 5),
]

# =========================================================
# 3. STYLES
# =========================================================

styles = getSampleStyleSheet()

center_style = ParagraphStyle(name="Center", parent=styles["Normal"], alignment=TA_CENTER)
right_style = ParagraphStyle(name="Right", parent=styles["Normal"], alignment=TA_RIGHT)

# 🔥 NEW: Table text style (for wrapping)
table_text_style = ParagraphStyle(
    name="TableText",
    fontName="Helvetica",
    fontSize=7,
    leading=8,
    wordWrap='CJK'   # ✅ handles long continuous text
)

# =========================================================
# 4. STATIC ELEMENTS
# =========================================================

logo = Image("logo.png")
logo._restrictSize((WIDTH_INCH - 0.5) * 72, 35 * mm)
logo.hAlign = 'CENTER'

solid_line = HRFlowable(width="100%", thickness=1)
dotted_line = HRFlowable(width="100%", thickness=1, dash=(2, 2))

footer_text = Paragraph("Thank You! Visit Again", center_style)

barcode = code128.Code128(bill_no, barHeight=15*mm, barWidth=0.4)
barcode.hAlign = 'CENTER'

# =========================================================
# 5. TABLE BUILD
# =========================================================

usable_width = width_mm * mm - ((LEFT_MARGIN + RIGHT_MARGIN) * mm)
# slightly wider item column
ratios = [0.07, 0.29, 0.14, 0.10, 0.12, 0.12, 0.16]
col_widths = [usable_width * r for r in ratios]
table_data = [["S.No", "Item", "Price", "Qty", "Meter", "Disc", "Total"]]

subtotal = 0

for i, (name, price, qty, is_shirt, meter, discount) in enumerate(items, start=1):
    item_total = price * qty - discount
    subtotal += item_total

    table_data.append([
        str(i),
        Paragraph(name, table_text_style),  # wrapped item
        f"{price:.2f}",                     # ✅ NEW PRICE COLUMN
        str(qty),
        f"{meter}" if is_shirt else "-",
        f"{discount}",
        f"{item_total:.2f}"
    ])

table = Table(table_data, colWidths=col_widths)

table.setStyle(TableStyle([
    ("FONT", (0,0), (-1,-1), "Helvetica"),
    ("FONTSIZE", (0,0), (-1,-1), 7),

    ("FONT", (0,0), (-1,0), "Helvetica-Bold"),
    ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),

    ("ALIGN", (0,0), (0,-1), "CENTER"),   # S.No
    ("ALIGN", (1,0), (1,-1), "LEFT"),     # Item
    ("ALIGN", (2,0), (2,-1), "RIGHT"),    # Price ✅
    ("ALIGN", (3,0), (3,-1), "CENTER"),   # Qty
    ("ALIGN", (4,0), (4,-1), "CENTER"),   # Meter
    ("ALIGN", (5,0), (5,-1), "CENTER"),   # Disc
    ("ALIGN", (6,0), (6,-1), "RIGHT"),    # Total

    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("GRID", (0,0), (-1,-1), 0.3, colors.grey),
]))

# =========================================================
# 6. GST CALCULATION
# =========================================================

sgst = subtotal * 0.025
cgst = subtotal * 0.025
grand_total = subtotal + sgst + cgst

# =========================================================
# 7. CONTENT BUILD
# =========================================================

content = []

content.append(logo)
content.append(Paragraph(f"<b>{shop_name}</b>", center_style))
content.append(Paragraph(shop_address, center_style))
content.append(Paragraph(phone, center_style))
content.append(Paragraph(gst, center_style))

content.append(solid_line)
content.append(Paragraph("<b>Tax Invoice / Receipt</b>", center_style))
content.append(solid_line)

content.append(Paragraph(bill_no))
content.append(Paragraph(date_time))

content.append(solid_line)
content.append(Spacer(1, 4))

content.append(table)

content.append(Spacer(1, 5))
content.append(solid_line)

# BILL SUMMARY
content.append(Paragraph(f"Subtotal : Rs {subtotal:.2f}", right_style))
content.append(Paragraph(f"SGST (2.5%) : Rs {sgst:.2f}", right_style))
content.append(Paragraph(f"CGST (2.5%) : Rs {cgst:.2f}", right_style))

content.append(dotted_line)

content.append(Paragraph(
    f"<b>Grand Total : Rs {grand_total:.2f}</b>",
    right_style
))

content.append(dotted_line)
content.append(Spacer(1, 6))

content.append(footer_text)

content.append(Spacer(1, 8))
content.append(barcode)
content.append(Paragraph(bill_no, center_style))

# =========================================================
# 8. DYNAMIC HEIGHT
# =========================================================

def calculate_height(content, width):
    total_height = 0
    for flowable in content:
        w, h = flowable.wrap(width, 1000)
        total_height += h
    return total_height

for flowable in content:
    flowable.wrapOn(None, width_mm * mm, 1000)

final_height = calculate_height(content, width_mm * mm) + 30

# =========================================================
# 9. CREATE PDF
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