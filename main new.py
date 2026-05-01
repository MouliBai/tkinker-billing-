# Import required modules
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Image, Table, TableStyle
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.graphics.barcode import code128, qr
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from datetime import datetime
import math

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
    ("AppleAppleAppleAppleAppleAppleAppleApple", 50, 2, False, 0),
    ("BananaBananaBananaBananaBananaBanana", 30, 1, False, 0),
    ("Shirt Piece", 200, 1, True, 2.5),
    ("Pant Piece", 300, 1, True, 3.0),
    ("Milk", 60, 1, False, 0),
]

# =========================================================
# 3. STYLES
# =========================================================

styles = getSampleStyleSheet()
center_style = ParagraphStyle(name="Center", parent=styles["Normal"], alignment=TA_CENTER)
right_style = ParagraphStyle(name="Right", parent=styles["Normal"], alignment=TA_RIGHT)
left_style = ParagraphStyle(
    name="Left",
    parent=styles["Normal"],
    alignment=TA_LEFT,
    fontSize=10
)

table_text_style = ParagraphStyle(
    name="TableText",
    fontName="Helvetica",
    fontSize=8,
    leading=12,
    wordWrap='CJK'
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

ratios = [0.08, 0.40, 0.14, 0.10, 0.12, 0.16]
col_widths = [usable_width * r for r in ratios]

table_data = [["S.No", "Item", "Price", "Qty", "Mtr", "Total"]]

subtotal = 0

for i, (name, price, qty, is_cloth, meter) in enumerate(items, start=1):
    if is_cloth:
        item_total = price * meter
    else:
        item_total = price * qty

    subtotal += item_total

    table_data.append([
        str(i),
        Paragraph(name, table_text_style),
        f"{price:.2f}",
        str(qty),
        f"{meter}" if is_cloth else "-",
        f"{item_total:.2f}"
    ])

table = Table(table_data, colWidths=col_widths)

table.setStyle(TableStyle([
    ("FONT", (0,0), (-1,-1), "Helvetica"),
    ("FONTSIZE", (0,0), (-1,-1), 9),

    ("FONT", (0,0), (-1,0), "Helvetica-Bold"),
    ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),

    ("ALIGN", (0,0), (0,-1), "CENTER"),
    ("ALIGN", (1,0), (1,-1), "LEFT"),
    ("ALIGN", (2,0), (2,-1), "RIGHT"),
    ("ALIGN", (3,0), (3,-1), "CENTER"),
    ("ALIGN", (4,0), (4,-1), "CENTER"),
    ("ALIGN", (5,0), (5,-1), "RIGHT"),

    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("GRID", (0,0), (-1,-1), 0.3, colors.white), #table color
]))

#------ two value in single line

bill_row = [
    Paragraph(bill_no, left_style),
    Paragraph(date_time, right_style)
]

bill_table = Table([bill_row], colWidths=[usable_width*0.5, usable_width*0.5])

bill_table.setStyle(TableStyle([
    ("LEFTPADDING", (0,0), (-1,-1), 0),
    ("RIGHTPADDING", (0,0), (-1,-1), 0),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
]))

# =========================================================
# 6. DISCOUNT + SAVINGS
# =========================================================

extra_discount = 0
discounted_total = subtotal - extra_discount

# 👉 YOU SAVED
you_saved = extra_discount

# =========================================================
# 7. GST + ROUND OFF
# =========================================================

sgst = discounted_total * 0.025
cgst = discounted_total * 0.025

gross_total = discounted_total + sgst + cgst

# 👉 ROUND OFF
rounded_total = round(gross_total)
round_off = rounded_total - gross_total

# =========================================================
# 8. UPI QR CODE
# =========================================================

upi_id = "baimouli-2@okaxis"
if upi_id:
    upi_link = f"upi://pay?pa={upi_id}&pn=EvoAura&am={rounded_total}&cu=INR"

    qr_code = qr.QrCodeWidget(upi_link)
    bounds = qr_code.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]

    d = Drawing(80, 80, transform=[80/width,0,0,80/height,0,0])
    d.add(qr_code)
    d.hAlign = 'CENTER'

# =========================================================
# 9. CONTENT BUILD
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

content.append(bill_table)

content.append(solid_line)
content.append(Spacer(1, 4))

content.append(table)

content.append(Spacer(1, 5))
content.append(solid_line)

# SUMMARY
content.append(Paragraph(f"Subtotal : Rs {subtotal:.2f}", right_style))

if extra_discount > 0:
    content.append(Paragraph(f"Discount : - Rs {extra_discount:.2f}", right_style))

content.append(Paragraph(f"SGST (2.5%) : Rs {sgst:.2f}", left_style))
content.append(Paragraph(f"CGST (2.5%) : Rs {cgst:.2f}", left_style))

content.append(Paragraph(f"Round Off : Rs {round_off:.2f}", right_style))

content.append(dotted_line)

content.append(Paragraph(
    f"<b>Grand Total : Rs {rounded_total:.2f}</b>",
    right_style
))

content.append(dotted_line)
content.append(Spacer(1, 6))

# 👉 QR CODE
if upi_id:
    content.append(Paragraph("Scan & Pay", center_style))
    content.append(d)



if extra_discount > 0:
    content.append(dotted_line)
    content.append(Spacer(1, 6))
    content.append(Paragraph(f"You Saved : Rs {you_saved:.2f}", right_style))

content.append(Spacer(1, 6))
content.append(solid_line)

content.append(Spacer(1, 6))

content.append(footer_text)
content.append(solid_line)

content.append(Spacer(1, 8))
content.append(barcode)
content.append(Paragraph(bill_no, center_style))
content.append(Spacer(1, 8))
content.append(footer_text)


# =========================================================
# 10. DYNAMIC HEIGHT
# =========================================================

def calculate_height(content, width):
    total_height = 0
    for flowable in content:
        w, h = flowable.wrap(width, 1000)
        total_height += h
    return total_height

for flowable in content:
    flowable.wrapOn(None, width_mm * mm, 1000)

final_height = calculate_height(content, width_mm * mm) + 40

# =========================================================
# 11. CREATE PDF
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