# Import required modules
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

# -----------------------------
# 1. INITIALIZE VALUES
# -----------------------------

WIDTH_INCH = 4
width_mm = WIDTH_INCH * 25.4  # convert inch to mm

shop_name = "My Shop"
shop_address = "Salem, Tamil Nadu"

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
    ("Eggs", 70),

]

total_amount = sum(price for name, price in items)

line_height_mm = 6
extra_lines = 1  # for header, total, and footer
height_mm = (len(items) + extra_lines) * line_height_mm

# 1. Create styles FIRST
styles = getSampleStyleSheet()

# 2. Then create custom style
center_style = ParagraphStyle(
    name="Center",
    parent=styles["Normal"],
    alignment=TA_CENTER
)

# -----------------------------
# 2. CREATE PDF
# -----------------------------

doc = SimpleDocTemplate(
    "receipt.pdf",
    pagesize=(width_mm * mm, height_mm * mm),
    leftMargin=5,
    rightMargin=5,
    topMargin=5,
    bottomMargin=5
)

styles = getSampleStyleSheet()
content = []

# -----------------------------
# 3. BUILD CONTENT
# -----------------------------

#Image("logo.png")
#content.append(Image("logo.png", width=1526, height=1024, hAlign='CENTER'))  # Centered logo at the top

# Create image object
img = Image("logo.png")

# Restrict max size (4 inch width, e.g., 40mm height limit)
img._restrictSize(4 * 72, 40 * mm)  # 4 inch = 288 points

# Center align
img.hAlign = 'CENTER'
content.append(img)  # Add image to content


# Shop name
#content.append(Paragraph(f"<b>{shop_name}</b>", styles["Title"]))

# Address
content.append(Paragraph(shop_address, center_style))

# FULL WIDTH LINE
content.append(HRFlowable(width="100%", thickness=1))

# Small space
content.append(Spacer(1, 4))

# Items
for name, price in items:
    line = f"{name}    Rs {price}"
    content.append(Paragraph(line, styles["Normal"]))

# Line before total
content.append(Spacer(1, 4))
content.append(HRFlowable(width="100%", thickness=1))

# Total
content.append(Paragraph(f"Total: Rs {total_amount}", styles["Normal"]))

# Final line
content.append(HRFlowable(width="100%", thickness=1, dash=(2, 2)))

# Footer
content.append(Paragraph("Thank You! Visit Again", styles["Normal"]))

# -----------------------------
# 4. BUILD PDF
# -----------------------------

doc.build(content)