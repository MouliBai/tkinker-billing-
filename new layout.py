# Import required modules
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet

# -----------------------------
# 1. INITIAL DATA (DERIVED FIRST)
# -----------------------------

WIDTH_INCH = 4
width_mm = WIDTH_INCH * 25.4  # convert inch → mm

# Shop details
shop_name = "Nikhitas Garments"
address = "BANGALORE - 560040, Karnataka."
phone = "Phone : 9845762133"
gst = "GSTIN : 29YKCVIZ80BS1Z0"

# Invoice details
bill_no = "INV18/22-23"
date = "19-03-2025, 04:50 PM"
customer = "Harish, Mysore"

# Items list (structured)
items = [
    {"name": "Rayon Kurti", "qty": "1 Nos", "amt": 430.00},
    {"name": "Cotton Saree\n<font size=8>Color : Red</font>", "qty": "1 Nos", "amt": 900.00},
    {"name": "Party Wear Kids Bo", "qty": "1 Nos", "amt": 750.00},
]

# Calculate subtotal
subtotal = sum(item["amt"] for item in items)

# Tax calculation
cgst = round(subtotal * 0.09, 2)
sgst = round(subtotal * 0.09, 2)

# Final total
grand_total = subtotal  # already tax included in your sample

# -----------------------------
# 2. CREATE PDF
# -----------------------------

doc = SimpleDocTemplate(
    "invoice.pdf",
    pagesize=(width_mm * mm, 500 * mm),  # large height (auto cut feel)
    leftMargin=5,
    rightMargin=5,
    topMargin=5,
    bottomMargin=0
)

styles = getSampleStyleSheet()
content = []

# -----------------------------
# 3. HEADER SECTION
# -----------------------------

content.append(Paragraph(f"<b>{shop_name}</b>", styles["Title"]))  # Shop name bold
content.append(Paragraph(address, styles["Normal"]))              # Address
content.append(Paragraph(phone, styles["Normal"]))                # Phone
content.append(Paragraph(gst, styles["Normal"]))                  # GST

content.append(HRFlowable(width="100%", thickness=1))             # Line separator

content.append(Paragraph("<b>Tax Invoice</b>", styles["Normal"])) # Title

# -----------------------------
# 4. BILL INFO
# -----------------------------

content.append(Paragraph(f"Bill No: <b>{bill_no}</b>", styles["Normal"]))
content.append(Paragraph(f"Date: {date}", styles["Normal"]))
content.append(Paragraph(customer, styles["Normal"]))

content.append(HRFlowable(width="100%", thickness=0.7, dash=(2,2)))  # Dotted line

# -----------------------------
# 5. ITEM TABLE
# -----------------------------

# Table header
table_data = [
    ["Item", "Qty", "Amt"]
]

# Add items dynamically
for i, item in enumerate(items, start=1):
    table_data.append([
        f"{i}. {item['name']}",   # Serial + name
        item["qty"],             # Quantity
        f"{item['amt']:.2f}"     # Amount formatted
    ])

# Create table
table = Table(table_data, colWidths=[60*mm, 20*mm, 20*mm])

# Style table
table.setStyle(TableStyle([
    ("FONT", (0,0), (-1,-1), "Helvetica"),
    ("FONTSIZE", (0,0), (-1,-1), 8),
    ("ALIGN", (1,1), (-1,-1), "RIGHT"),  # Qty & Amt right align
    ("LINEBELOW", (0,0), (-1,0), 1, colors.black),  # Header underline
]))

content.append(table)

content.append(HRFlowable(width="100%", thickness=0.7, dash=(2,2)))

# -----------------------------
# 6. SUBTOTAL + TAX
# -----------------------------

content.append(Paragraph(f"(Tax Incl) Sub Total    {subtotal:.2f}", styles["Normal"]))
content.append(Paragraph(f"CGST 9% on {subtotal:.2f}        {cgst:.2f}", styles["Normal"]))
content.append(Paragraph(f"SGST 9% on {subtotal:.2f}        {sgst:.2f}", styles["Normal"]))

content.append(HRFlowable(width="100%", thickness=1))

# -----------------------------
# 7. TOTAL SECTION
# -----------------------------

content.append(Paragraph(f"<b>TOTAL    Rs. {grand_total:.2f}</b>", styles["Title"]))

content.append(Paragraph("Available Points (Added) : 208", styles["Normal"]))

# -----------------------------
# 8. BANK DETAILS
# -----------------------------

content.append(Spacer(1, 5))

content.append(Paragraph("<b>Our Bank Details</b>", styles["Normal"]))
content.append(Paragraph("Account No : 9875645632232", styles["Normal"]))
content.append(Paragraph("Account Name : NIKHITAS", styles["Normal"]))
content.append(Paragraph("IFSC Code : ICICI000458976", styles["Normal"]))
content.append(Paragraph("Bank : ICICI", styles["Normal"]))
content.append(Paragraph("Branch : BANDIPUR", styles["Normal"]))

# -----------------------------
# 9. BUILD PDF
# -----------------------------

doc.build(content)