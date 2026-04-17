# Tally Style Invoice PDF Generator (Thermal Friendly + A4 Option)
# Professional layout inspired by Tally invoice
# Uses reportlab

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from datetime import datetime

# -----------------------------
# CONFIGURATION
# -----------------------------

# Choose layout: 'thermal_3', 'thermal_4', 'A4'
layout_type = 'thermal_3'

if layout_type == 'thermal_3':
    PAGE_SIZE = (3 * inch, 8 * inch)
elif layout_type == 'thermal_4':
    PAGE_SIZE = (4 * inch, 10 * inch)
else:
    PAGE_SIZE = A4

styles = getSampleStyleSheet()

# -----------------------------
# SAMPLE DATA
# -----------------------------

data = {
    "company": "My Store Pvt Ltd",
    "address": "123 Street, Salem, Tamil Nadu",
    "gst": "33ABCDE1234F1Z5",
    "phone": "9876543210",
    "invoice_no": "INV1001",
    "date": datetime.now().strftime("%d-%m-%Y %H:%M"),
    "customer": "Walk-in Customer",
    "items": [
        {"name": "Product 1", "qty": 2, "rate": 50, "gst": 5},
        {"name": "Product 2", "qty": 1, "rate": 100, "gst": 12}
    ],
    "footer": "Thank you! Visit again"
}

# -----------------------------
# CALCULATIONS
# -----------------------------

def calculate_items(items):
    table_data = [["Item", "Qty", "Rate", "GST%", "Amount"]]
    total = 0

    for item in items:
        qty = item["qty"]
        rate = item["rate"]
        gst = item["gst"]

        base = qty * rate
        gst_amt = base * gst / 100
        amount = base + gst_amt

        total += amount

        table_data.append([
            item["name"],
            str(qty),
            str(rate),
            str(gst),
            f"{amount:.2f}"
        ])

    return table_data, total

# -----------------------------
# PDF GENERATOR
# -----------------------------

def generate_tally_pdf(data, filename="tally_invoice.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=PAGE_SIZE, leftMargin=10, rightMargin=10)
    elements = []

    # Header
    elements.append(Paragraph("<b>TAX INVOICE</b>", styles['Title']))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(f"<b>{data['company']}</b>", styles['Normal']))
    elements.append(Paragraph(data['address'], styles['Normal']))
    elements.append(Paragraph(f"GST: {data['gst']}", styles['Normal']))
    elements.append(Paragraph(f"Phone: {data['phone']}", styles['Normal']))

    elements.append(Spacer(1, 10))

    # Invoice Info
    elements.append(Paragraph(f"Invoice No: {data['invoice_no']}", styles['Normal']))
    elements.append(Paragraph(f"Date: {data['date']}", styles['Normal']))
    elements.append(Paragraph(f"Customer: {data['customer']}", styles['Normal']))

    elements.append(Spacer(1, 10))

    # Table
    table_data, total = calculate_items(data['items'])

    table = Table(table_data, repeatRows=1)

    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('ALIGN', (1,1), (-1,-1), 'CENTER')
    ]))

    elements.append(table)

    elements.append(Spacer(1, 10))

    # Total
    elements.append(Paragraph(f"<b>Total: {total:.2f}</b>", styles['Normal']))

    elements.append(Spacer(1, 10))

    # Footer
    elements.append(Paragraph(data['footer'], styles['Normal']))

    doc.build(elements)


# -----------------------------
# RUN
# -----------------------------

generate_tally_pdf(data)
print("Tally-style invoice PDF generated!")


# -----------------------------
# TEST CASES
# -----------------------------

def test_pdf():
    generate_tally_pdf(data, "test_tally.pdf")


def test_empty():
    temp = data.copy()
    temp['items'] = []
    generate_tally_pdf(temp, "test_empty.pdf")


if __name__ == "__main__":
    test_pdf()
    test_empty()
    print("All tests passed!")
