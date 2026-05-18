import sys
import sqlite3

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QMessageBox, QDialog,
    QGridLayout, QComboBox, QAbstractItemView,
    QListWidget, QListWidgetItem, QCheckBox,
    QTabWidget, QScrollArea, QDateEdit, QDoubleSpinBox,
    QSpinBox, QTextEdit, QSizePolicy, QApplication
)
from PyQt5.QtGui import QFont, QColor, QBrush, QIcon, QPalette
from PyQt5.QtCore import Qt, QDate


# ─────────────────────────────────────────────────────────
#  STYLE CONSTANTS
# ─────────────────────────────────────────────────────────
PRIMARY   = "#1a7fe8"
DANGER    = "#e53935"
BG_LIGHT  = "#f4f7fb"
WHITE     = "#ffffff"
BORDER    = "#e0e8f0"

FIELD_STYLE = """
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit {
        border: 1px solid #c8d8ea;
        border-radius: 6px;
        padding: 5px 9px;
        font-size: 13px;
        background: white;
        color: #222;
        min-height: 30px;
    }
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus,
    QDoubleSpinBox:focus, QDateEdit:focus, QTextEdit:focus {
        border: 1.5px solid #1a7fe8;
        background: #f8fbff;
    }
    QLineEdit:read-only { background: #f5f5f5; color: #888; }
    QComboBox::drop-down { border: none; }
    QComboBox::down-arrow { image: none; width: 0; }
    QCheckBox { font-size: 13px; color: #333; }
    QCheckBox::indicator { width: 16px; height: 16px; border-radius: 4px;
        border: 1px solid #aaa; background: white; }
    QCheckBox::indicator:checked { background: #1a7fe8; border-color: #1a7fe8; }
"""

LABEL_STYLE  = "font-size: 12px; color: #666; font-weight: 500;"
REQ_STYLE    = "font-size: 12px; color: #e53935; font-weight: 600;"
HINT_STYLE   = "font-size: 11px; color: #aaa; margin-top: 1px;"
SEC_STYLE    = """
    QFrame#section {
        background: white;
        border: 1px solid #e8eef5;
        border-radius: 10px;
    }
"""
TAB_STYLE = """
    QTabWidget::pane {
        border: none;
        background: #f4f7fb;
    }
    QTabBar::tab {
        background: #eef2f8;
        color: #555;
        padding: 8px 18px;
        border-radius: 6px;
        margin-right: 4px;
        font-size: 12px;
        font-weight: 500;
    }
    QTabBar::tab:selected {
        background: #1a7fe8;
        color: white;
    }
    QTabBar::tab:hover:!selected { background: #dde8f5; }
"""


# ─────────────────────────────────────────────────────────
#  DB FUNCTIONS
# ─────────────────────────────────────────────────────────
def init_product_table(db_name):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    # ── Create table if it doesn't exist (fresh install) ──────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            item_code         TEXT UNIQUE,
            name              TEXT NOT NULL,
            description       TEXT        DEFAULT '',
            category          TEXT        DEFAULT '',
            sub_category      TEXT        DEFAULT '',
            brand             TEXT        DEFAULT '',
            manufacturer      TEXT        DEFAULT '',
            hsn_code          TEXT        DEFAULT '',
            barcode           TEXT        DEFAULT '',
            unit              TEXT        DEFAULT '',
            pack_size         INTEGER     DEFAULT 1,
            meter             TEXT        DEFAULT '',
            purchase_price    REAL        DEFAULT 0,
            selling_price     REAL        DEFAULT 0,
            wholesale_price   REAL        DEFAULT 0,
            min_selling_price REAL        DEFAULT 0,
            discount_pct      REAL        DEFAULT 0,
            tax_inclusive     INTEGER     DEFAULT 0,
            gst_rate          TEXT        DEFAULT '0%',
            tax_type          TEXT        DEFAULT 'CGST+SGST',
            cess_pct          REAL        DEFAULT 0,
            opening_stock     INTEGER     DEFAULT 0,
            stock             INTEGER     DEFAULT 0,
            reorder_level     INTEGER     DEFAULT 0,
            min_order_qty     INTEGER     DEFAULT 1,
            max_stock         INTEGER     DEFAULT 0,
            warehouse         TEXT        DEFAULT '',
            rack_location     TEXT        DEFAULT '',
            track_batch       INTEGER     DEFAULT 0,
            track_expiry      INTEGER     DEFAULT 0,
            mfg_date          TEXT        DEFAULT '',
            expiry_date       TEXT        DEFAULT '',
            expiry_alert_days INTEGER     DEFAULT 30,
            is_returnable     INTEGER     DEFAULT 1,
            allow_neg_stock   INTEGER     DEFAULT 0,
            supplier_name     TEXT        DEFAULT '',
            supplier_code     TEXT        DEFAULT '',
            lead_time_days    INTEGER     DEFAULT 0,
            last_purchase_price REAL      DEFAULT 0,
            weight_kg         REAL        DEFAULT 0,
            length_cm         REAL        DEFAULT 0,
            width_cm          REAL        DEFAULT 0,
            height_cm         REAL        DEFAULT 0,
            has_variants      INTEGER     DEFAULT 0,
            variant_type      TEXT        DEFAULT '',
            internal_notes    TEXT        DEFAULT '',
            status            TEXT        DEFAULT 'Active'
        )
    """)

    # ── Auto-migrate: add any missing columns to an existing old-schema DB ─
    # This handles users upgrading from the previous 9-column schema.
    c.execute("PRAGMA table_info(products)")
    existing_cols = {row[1] for row in c.fetchall()}

    new_columns = [
        ("description",         "TEXT        DEFAULT ''"),
        ("sub_category",        "TEXT        DEFAULT ''"),
        ("brand",               "TEXT        DEFAULT ''"),
        ("manufacturer",        "TEXT        DEFAULT ''"),
        ("hsn_code",            "TEXT        DEFAULT ''"),
        ("barcode",             "TEXT        DEFAULT ''"),
        ("pack_size",           "INTEGER     DEFAULT 1"),
        ("purchase_price",      "REAL        DEFAULT 0"),
        ("selling_price",       "REAL        DEFAULT 0"),
        ("wholesale_price",     "REAL        DEFAULT 0"),
        ("min_selling_price",   "REAL        DEFAULT 0"),
        ("discount_pct",        "REAL        DEFAULT 0"),
        ("tax_inclusive",       "INTEGER     DEFAULT 0"),
        ("gst_rate",            "TEXT        DEFAULT '0%'"),
        ("tax_type",            "TEXT        DEFAULT 'CGST+SGST'"),
        ("cess_pct",            "REAL        DEFAULT 0"),
        ("opening_stock",       "INTEGER     DEFAULT 0"),
        ("reorder_level",       "INTEGER     DEFAULT 0"),
        ("min_order_qty",       "INTEGER     DEFAULT 1"),
        ("max_stock",           "INTEGER     DEFAULT 0"),
        ("warehouse",           "TEXT        DEFAULT ''"),
        ("rack_location",       "TEXT        DEFAULT ''"),
        ("track_batch",         "INTEGER     DEFAULT 0"),
        ("track_expiry",        "INTEGER     DEFAULT 0"),
        ("mfg_date",            "TEXT        DEFAULT ''"),
        ("expiry_date",         "TEXT        DEFAULT ''"),
        ("expiry_alert_days",   "INTEGER     DEFAULT 30"),
        ("is_returnable",       "INTEGER     DEFAULT 1"),
        ("allow_neg_stock",     "INTEGER     DEFAULT 0"),
        ("supplier_name",       "TEXT        DEFAULT ''"),
        ("supplier_code",       "TEXT        DEFAULT ''"),
        ("lead_time_days",      "INTEGER     DEFAULT 0"),
        ("last_purchase_price", "REAL        DEFAULT 0"),
        ("weight_kg",           "REAL        DEFAULT 0"),
        ("length_cm",           "REAL        DEFAULT 0"),
        ("width_cm",            "REAL        DEFAULT 0"),
        ("height_cm",           "REAL        DEFAULT 0"),
        ("has_variants",        "INTEGER     DEFAULT 0"),
        ("variant_type",        "TEXT        DEFAULT ''"),
        ("internal_notes",      "TEXT        DEFAULT ''"),
    ]

    for col_name, col_def in new_columns:
        if col_name not in existing_cols:
            c.execute(f"ALTER TABLE products ADD COLUMN {col_name} {col_def}")

    # ── Migrate old 'price' column → selling_price + purchase_price ───────
    # Old schema used 'price'; new schema uses 'selling_price'.
    # Copy values so existing product data is preserved.
    if "price" in existing_cols:
        c.execute("""
            UPDATE products
            SET selling_price  = price,
                purchase_price = price
            WHERE selling_price = 0 AND price > 0
        """)

    conn.commit()
    conn.close()


def get_all_products(db_name):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("""
        SELECT item_code, name, category, unit, meter,
               selling_price, stock, status, hsn_code, gst_rate
        FROM products ORDER BY item_code
    """)
    rows = c.fetchall()
    conn.close()
    return rows


def search_products(db_name, query):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("""
        SELECT item_code, name, category, unit, meter,
               selling_price, stock, status, hsn_code, gst_rate
        FROM products
        WHERE item_code LIKE ? OR name LIKE ?
        ORDER BY item_code
    """, (f"%{query}%", f"%{query}%"))
    rows = c.fetchall()
    conn.close()
    return rows


def search_suggestions(db_name, query):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("""
        SELECT item_code, name FROM products
        WHERE item_code LIKE ? OR name LIKE ?
        LIMIT 10
    """, (f"%{query}%", f"%{query}%"))
    rows = c.fetchall()
    conn.close()
    return rows


def get_next_item_code(db_name):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM products")
    count = c.fetchone()[0]
    conn.close()
    return f"P{str(count + 1).zfill(5)}"


def get_product_full(db_name, item_code):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE item_code=?", (item_code,))
    row = c.fetchone()
    col_names = [d[0] for d in c.description]
    conn.close()
    if row:
        return dict(zip(col_names, row))
    return None


def save_product(db_name, data: dict):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    try:
        cols = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        c.execute(
            f"INSERT INTO products ({cols}) VALUES ({placeholders})",
            list(data.values())
        )
        conn.commit()
        return True
    except Exception as e:
        print("Save error:", e)
        return False
    finally:
        conn.close()


def update_product(db_name, item_code, data: dict):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    set_clause = ", ".join([f"{k}=?" for k in data.keys()])
    c.execute(
        f"UPDATE products SET {set_clause} WHERE item_code=?",
        list(data.values()) + [item_code]
    )
    conn.commit()
    conn.close()


def delete_product(db_name, item_code):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE item_code=?", (item_code,))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────
#  HELPER: Section Card
# ─────────────────────────────────────────────────────────
def make_section(title: str, icon: str = "") -> tuple:
    """Returns (outer_frame, inner_layout) for a card section."""
    frame = QFrame()
    frame.setObjectName("section")
    frame.setStyleSheet(SEC_STYLE)
    outer = QVBoxLayout(frame)
    outer.setContentsMargins(18, 14, 18, 16)
    outer.setSpacing(12)

    hdr = QHBoxLayout()
    hdr.setSpacing(6)
    if icon:
        ico = QLabel(icon)
        ico.setStyleSheet("font-size: 15px; color: #1a7fe8;")
        hdr.addWidget(ico)
    lbl = QLabel(title)
    lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #1a3558;")
    hdr.addWidget(lbl)
    hdr.addStretch()
    outer.addLayout(hdr)

    sep = QFrame()
    sep.setFrameShape(QFrame.HLine)
    sep.setStyleSheet("background: #eef2f8; border: none; max-height: 1px;")
    outer.addWidget(sep)

    grid = QGridLayout()
    grid.setSpacing(8)
    grid.setColumnMinimumWidth(0, 130)
    grid.setColumnMinimumWidth(1, 160)
    grid.setColumnMinimumWidth(2, 130)
    grid.setColumnMinimumWidth(3, 160)
    outer.addLayout(grid)

    return frame, grid


def add_field(grid, row, col, label: str, widget,
              required=False, hint="", span=1):
    """Add label + widget to grid. span=2 means widget spans 3 extra cols."""
    lbl = QLabel(label)
    lbl.setStyleSheet(LABEL_STYLE)
    if required:
        lbl.setText(label + "  <span style='color:#e53935'>*</span>")
        lbl.setTextFormat(Qt.RichText)
    grid.addWidget(lbl, row, col)

    end_col = col + 1
    col_span = 1 + (span - 1) * 2
    grid.addWidget(widget, row, end_col, 1, col_span)

    if hint:
        h = QLabel(hint)
        h.setStyleSheet(HINT_STYLE)
        grid.addWidget(h, row + 1, end_col, 1, col_span)


# ─────────────────────────────────────────────────────────
#  ADD / EDIT PRODUCT DIALOG
# ─────────────────────────────────────────────────────────
class ProductDialog(QDialog):

    def __init__(self, db_name, item_code=None, parent=None):
        super().__init__(parent)
        self.db_name   = db_name
        self.edit_code = item_code          # None = Add
        self.prod      = get_product_full(db_name, item_code) if item_code else {}

        self.setWindowTitle("Edit Product" if item_code else "Add Product")
        self.setMinimumSize(820, 680)
        self.setStyleSheet(f"QDialog {{ background: {BG_LIGHT}; }}")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ──────────────────────────────
        hdr = QFrame()
        hdr.setFixedHeight(54)
        hdr.setStyleSheet(f"background: {PRIMARY}; border: none;")
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(20, 0, 20, 0)

        title_lbl = QLabel(
            "✏️  Edit Product" if item_code else "➕  Add New Product"
        )
        title_lbl.setStyleSheet(
            "color: white; font-size: 15px; font-weight: 700;"
        )
        hdr_lay.addWidget(title_lbl)
        hdr_lay.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet("""
            QPushButton { background: rgba(255,255,255,0.2); color: white;
                border-radius: 14px; font-size: 13px; border: none; }
            QPushButton:hover { background: rgba(255,255,255,0.35); }
        """)
        close_btn.clicked.connect(self.reject)
        hdr_lay.addWidget(close_btn)
        root.addWidget(hdr)

        # ── Tab widget ───────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TAB_STYLE)
        self.tabs.setContentsMargins(12, 12, 12, 0)

        self._build_tab_basic()
        self._build_tab_pricing()
        self._build_tab_inventory()
        self._build_tab_supplier()
        self._build_tab_extra()

        scroll_wrap = QScrollArea()
        scroll_wrap.setWidgetResizable(True)
        scroll_wrap.setFrameShape(QFrame.NoFrame)
        scroll_wrap.setStyleSheet("background: transparent;")
        tab_container = QWidget()
        tab_container.setStyleSheet("background: transparent;")
        tcl = QVBoxLayout(tab_container)
        tcl.setContentsMargins(12, 12, 12, 12)
        tcl.addWidget(self.tabs)
        scroll_wrap.setWidget(tab_container)
        root.addWidget(scroll_wrap, 1)

        # ── Footer ───────────────────────────────
        footer = QFrame()
        footer.setFixedHeight(58)
        footer.setStyleSheet(
            "background: white; border-top: 1px solid #e0e8f0;"
        )
        foot_lay = QHBoxLayout(footer)
        foot_lay.setContentsMargins(20, 0, 20, 0)
        foot_lay.setSpacing(10)
        foot_lay.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedSize(100, 36)
        btn_cancel.setStyleSheet("""
            QPushButton { background: #f0f0f0; color: #444;
                border-radius: 7px; font-size: 13px; font-weight: 600;
                border: none; }
            QPushButton:hover { background: #e0e0e0; }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton(
            "💾  Update" if item_code else "💾  Save Product"
        )
        btn_save.setFixedHeight(36)
        btn_save.setMinimumWidth(130)
        btn_save.setStyleSheet(f"""
            QPushButton {{ background: {PRIMARY}; color: white;
                border-radius: 7px; font-size: 13px; font-weight: 700;
                border: none; padding: 0 20px; }}
            QPushButton:hover {{ background: #1565c0; }}
        """)
        btn_save.clicked.connect(self._save)

        foot_lay.addWidget(btn_cancel)
        foot_lay.addWidget(btn_save)
        root.addWidget(footer)

        self._apply_styles()
        if self.prod:
            self._populate()

    # ── Apply FIELD_STYLE to all input widgets ──
    def _apply_styles(self):
        self.setStyleSheet(self.styleSheet() + FIELD_STYLE)

    # ─────────────────────────── TAB 1: BASIC ────────────────────────────
    def _build_tab_basic(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        # ── Identification ──────────────────────
        sec, grid = make_section("Identification & Basic Info", "🔖")

        self.f_item_code = QLineEdit()
        self.f_item_code.setPlaceholderText("e.g. P00001 or scan barcode")
        self.f_auto_code = QCheckBox("Auto-generate code")
        self.f_auto_code.stateChanged.connect(self._toggle_code)

        self.f_name = QLineEdit()
        self.f_name.setPlaceholderText("Product / item name")

        self.f_barcode = QLineEdit()
        self.f_barcode.setPlaceholderText("EAN / barcode number")

        self.f_hsn = QLineEdit()
        self.f_hsn.setPlaceholderText("e.g. 1006")

        r = 0
        add_field(grid, r, 0, "Item code", self.f_item_code, required=True)
        add_field(grid, r, 2, "Barcode / EAN", self.f_barcode)
        r += 1
        grid.addWidget(self.f_auto_code, r, 1)
        r += 1
        add_field(grid, r, 0, "Product name", self.f_name, required=True, span=2)
        r += 1
        add_field(grid, r, 0, "HSN code", self.f_hsn,
                  hint="Mandatory for GST filing")
        lay.addWidget(sec)

        # ── Classification ──────────────────────
        sec2, grid2 = make_section("Classification", "🗂️")

        self.f_category = QComboBox()
        self.f_category.setEditable(True)
        self.f_category.addItems([
            "", "Groceries", "Household", "Beverages",
            "Stationery", "Electronics", "Pharma",
            "Clothing", "Hardware", "Cosmetics"
        ])

        self.f_sub_cat = QLineEdit()
        self.f_sub_cat.setPlaceholderText("e.g. Rice & Grains")

        self.f_brand = QLineEdit()
        self.f_brand.setPlaceholderText("e.g. India Gate")

        self.f_manufacturer = QLineEdit()
        self.f_manufacturer.setPlaceholderText("e.g. KRBL Ltd.")

        self.f_unit = QComboBox()
        self.f_unit.setEditable(True)
        self.f_unit.addItems([
            "Pcs", "Kg", "g", "L", "ml", "Box",
            "Dozen", "Bag", "Strip", "Pack", "Nos"
        ])

        self.f_meter = QLineEdit()
        self.f_meter.setPlaceholderText("e.g. Piece(s), 10 Tablets")

        self.f_pack_size = QSpinBox()
        self.f_pack_size.setRange(1, 99999)
        self.f_pack_size.setValue(1)

        r2 = 0
        add_field(grid2, r2, 0, "Category", self.f_category)
        add_field(grid2, r2, 2, "Sub-category", self.f_sub_cat)
        r2 += 1
        add_field(grid2, r2, 0, "Brand", self.f_brand)
        add_field(grid2, r2, 2, "Manufacturer", self.f_manufacturer)
        r2 += 1
        add_field(grid2, r2, 0, "Unit of measure", self.f_unit)
        add_field(grid2, r2, 2, "Pack size (qty/pack)", self.f_pack_size)
        r2 += 1
        add_field(grid2, r2, 0, "Meter / display unit", self.f_meter,
                  hint="How it shows on invoice (e.g. '5 kg bag')", span=2)
        lay.addWidget(sec2)

        # ── Description ─────────────────────────
        sec3, grid3 = make_section("Description & Notes", "📝")
        self.f_desc = QTextEdit()
        self.f_desc.setPlaceholderText("Short product description...")
        self.f_desc.setFixedHeight(70)
        grid3.addWidget(QLabel("Description"), 0, 0)
        grid3.addWidget(self.f_desc, 0, 1, 1, 3)
        lay.addWidget(sec3)
        lay.addStretch()

        self.tabs.addTab(page, "🏷️  Basic Info")

    # ─────────────────────────── TAB 2: PRICING ──────────────────────────
    def _build_tab_pricing(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        # ── Pricing ─────────────────────────────
        sec, grid = make_section("Pricing", "💰")

        def spin(mx=999999): 
            s = QDoubleSpinBox()
            s.setRange(0, mx)
            s.setDecimals(2)
            s.setPrefix("₹ ")
            return s

        self.f_purchase_price    = spin()
        self.f_selling_price     = spin()
        self.f_wholesale_price   = spin()
        self.f_min_selling_price = spin()
        self.f_discount_pct = QDoubleSpinBox()
        self.f_discount_pct.setRange(0, 100)
        self.f_discount_pct.setDecimals(2)
        self.f_discount_pct.setSuffix(" %")

        self.f_tax_inclusive = QCheckBox("Price is tax-inclusive (includes GST)")

        r = 0
        add_field(grid, r, 0, "Purchase price (MRP)", self.f_purchase_price, required=True)
        add_field(grid, r, 2, "Selling price", self.f_selling_price, required=True)
        r += 1
        add_field(grid, r, 0, "Wholesale price", self.f_wholesale_price)
        add_field(grid, r, 2, "Min selling price",  self.f_min_selling_price,
                  hint="Floor — no sale below this")
        r += 1
        add_field(grid, r, 0, "Discount %", self.f_discount_pct)
        grid.addWidget(self.f_tax_inclusive, r, 2, 1, 2)
        lay.addWidget(sec)

        # ── GST & Tax ───────────────────────────
        sec2, grid2 = make_section("GST & Tax", "🧾")

        self.f_gst_rate = QComboBox()
        self.f_gst_rate.addItems(["0% — Exempt", "5%", "12%", "18%", "28%"])

        self.f_tax_type = QComboBox()
        self.f_tax_type.addItems(["CGST + SGST (local)", "IGST (interstate)"])

        self.f_cess_pct = QDoubleSpinBox()
        self.f_cess_pct.setRange(0, 100)
        self.f_cess_pct.setDecimals(2)
        self.f_cess_pct.setSuffix(" %")

        r2 = 0
        add_field(grid2, r2, 0, "GST rate", self.f_gst_rate, required=True)
        add_field(grid2, r2, 2, "Tax type", self.f_tax_type)
        r2 += 1
        add_field(grid2, r2, 0, "Cess %", self.f_cess_pct,
                  hint="For tobacco, luxury, etc.")
        lay.addWidget(sec2)
        lay.addStretch()

        self.tabs.addTab(page, "💰  Pricing & Tax")

    # ─────────────────────────── TAB 3: INVENTORY ────────────────────────
    def _build_tab_inventory(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        # ── Stock ────────────────────────────────
        sec, grid = make_section("Stock Levels", "📦")

        self.f_opening_stock = QSpinBox()
        self.f_opening_stock.setRange(0, 9999999)
        self.f_reorder_level = QSpinBox()
        self.f_reorder_level.setRange(0, 9999999)
        self.f_min_order_qty = QSpinBox()
        self.f_min_order_qty.setRange(1, 999999)
        self.f_min_order_qty.setValue(1)
        self.f_max_stock = QSpinBox()
        self.f_max_stock.setRange(0, 9999999)
        self.f_allow_neg = QCheckBox("Allow negative stock (bill even if stock = 0)")

        r = 0
        add_field(grid, r, 0, "Opening stock", self.f_opening_stock, required=True)
        add_field(grid, r, 2, "Reorder level",  self.f_reorder_level,
                  hint="Alert when stock falls below")
        r += 1
        add_field(grid, r, 0, "Min order qty", self.f_min_order_qty)
        add_field(grid, r, 2, "Max stock limit", self.f_max_stock)
        r += 1
        grid.addWidget(self.f_allow_neg, r, 0, 1, 4)
        lay.addWidget(sec)

        # ── Location ────────────────────────────
        sec2, grid2 = make_section("Storage Location", "🏬")

        self.f_warehouse = QComboBox()
        self.f_warehouse.setEditable(True)
        self.f_warehouse.addItems(
            ["Main store", "Warehouse A", "Warehouse B", "Cold storage"]
        )
        self.f_rack = QLineEdit()
        self.f_rack.setPlaceholderText("e.g. A3-R2-S4")

        r2 = 0
        add_field(grid2, r2, 0, "Warehouse / location", self.f_warehouse)
        add_field(grid2, r2, 2, "Rack / shelf", self.f_rack)
        lay.addWidget(sec2)

        # ── Batch & Expiry ───────────────────────
        sec3, grid3 = make_section("Batch & Expiry Tracking", "📅")

        self.f_track_batch  = QCheckBox("Track batch numbers")
        self.f_track_expiry = QCheckBox("Track expiry dates")

        self.f_mfg_date = QDateEdit()
        self.f_mfg_date.setCalendarPopup(True)
        self.f_mfg_date.setDate(QDate.currentDate())
        self.f_mfg_date.setDisplayFormat("dd-MM-yyyy")

        self.f_expiry_date = QDateEdit()
        self.f_expiry_date.setCalendarPopup(True)
        self.f_expiry_date.setDate(QDate.currentDate().addYears(1))
        self.f_expiry_date.setDisplayFormat("dd-MM-yyyy")

        self.f_expiry_alert = QSpinBox()
        self.f_expiry_alert.setRange(1, 365)
        self.f_expiry_alert.setValue(30)
        self.f_expiry_alert.setSuffix(" days before")

        self.f_returnable = QCheckBox("Product is returnable")
        self.f_returnable.setChecked(True)

        r3 = 0
        grid3.addWidget(self.f_track_batch,  r3, 0, 1, 2)
        grid3.addWidget(self.f_track_expiry, r3, 2, 1, 2)
        r3 += 1
        add_field(grid3, r3, 0, "Manufacturing date", self.f_mfg_date)
        add_field(grid3, r3, 2, "Expiry date",         self.f_expiry_date)
        r3 += 1
        add_field(grid3, r3, 0, "Expiry alert",  self.f_expiry_alert,
                  hint="Get notified N days before expiry")
        grid3.addWidget(self.f_returnable, r3, 2, 1, 2)
        lay.addWidget(sec3)
        lay.addStretch()

        self.tabs.addTab(page, "📦  Inventory")

    # ─────────────────────────── TAB 4: SUPPLIER ─────────────────────────
    def _build_tab_supplier(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        sec, grid = make_section("Supplier / Vendor Details", "🚚")

        self.f_supplier_name = QComboBox()
        self.f_supplier_name.setEditable(True)
        self.f_supplier_name.addItems([
            "", "AK Wholesale", "Sri Balaji Traders",
            "Ramesh & Co.", "Lakshmi Distributors"
        ])
        self.f_supplier_code = QLineEdit()
        self.f_supplier_code.setPlaceholderText("Supplier's own SKU / code")

        self.f_lead_time = QSpinBox()
        self.f_lead_time.setRange(0, 365)
        self.f_lead_time.setSuffix(" days")

        self.f_last_purchase = QDoubleSpinBox()
        self.f_last_purchase.setRange(0, 9999999)
        self.f_last_purchase.setDecimals(2)
        self.f_last_purchase.setPrefix("₹ ")

        r = 0
        add_field(grid, r, 0, "Primary supplier", self.f_supplier_name)
        add_field(grid, r, 2, "Supplier product code", self.f_supplier_code)
        r += 1
        add_field(grid, r, 0, "Lead time", self.f_lead_time,
                  hint="Days to restock from supplier")
        add_field(grid, r, 2, "Last purchase price", self.f_last_purchase)
        lay.addWidget(sec)
        lay.addStretch()

        self.tabs.addTab(page, "🚚  Supplier")

    # ─────────────────────────── TAB 5: EXTRA ────────────────────────────
    def _build_tab_extra(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        # ── Physical ────────────────────────────
        sec, grid = make_section("Physical Dimensions", "📐")

        self.f_weight = QDoubleSpinBox()
        self.f_weight.setRange(0, 9999)
        self.f_weight.setDecimals(3)
        self.f_weight.setSuffix(" kg")

        self.f_length = QDoubleSpinBox()
        self.f_length.setRange(0, 9999)
        self.f_length.setSuffix(" cm")

        self.f_width = QDoubleSpinBox()
        self.f_width.setRange(0, 9999)
        self.f_width.setSuffix(" cm")

        self.f_height = QDoubleSpinBox()
        self.f_height.setRange(0, 9999)
        self.f_height.setSuffix(" cm")

        r = 0
        add_field(grid, r, 0, "Weight",  self.f_weight)
        add_field(grid, r, 2, "Length",  self.f_length)
        r += 1
        add_field(grid, r, 0, "Width",   self.f_width)
        add_field(grid, r, 2, "Height",  self.f_height)
        lay.addWidget(sec)

        # ── Variants ────────────────────────────
        sec2, grid2 = make_section("Variants", "🔀")

        self.f_has_variants = QCheckBox("This product has variants (e.g. size, colour, weight)")
        self.f_variant_type = QComboBox()
        self.f_variant_type.setEditable(True)
        self.f_variant_type.addItems(["Size", "Weight", "Colour", "Flavour", "Custom"])

        grid2.addWidget(self.f_has_variants, 0, 0, 1, 4)
        add_field(grid2, 1, 0, "Variant type", self.f_variant_type)
        lay.addWidget(sec2)

        # ── Status & flags ──────────────────────
        sec3, grid3 = make_section("Status & Flags", "⚙️")

        self.f_status = QComboBox()
        self.f_status.addItems(["Active", "Draft", "Inactive", "Discontinued"])

        self.f_notes = QTextEdit()
        self.f_notes.setPlaceholderText("Internal notes (visible to staff only)...")
        self.f_notes.setFixedHeight(70)

        r3 = 0
        add_field(grid3, r3, 0, "Product status", self.f_status, required=True)
        r3 += 1
        grid3.addWidget(QLabel("Internal notes"), r3, 0)
        grid3.addWidget(self.f_notes, r3, 1, 1, 3)
        lay.addWidget(sec3)
        lay.addStretch()

        self.tabs.addTab(page, "⚙️  Extra")

    # ─────────────────────────── HELPERS ─────────────────────────────────
    def _toggle_code(self, state):
        if state:
            code = get_next_item_code(self.db_name)
            self.f_item_code.setText(code)
            self.f_item_code.setReadOnly(True)
        else:
            self.f_item_code.setText("")
            self.f_item_code.setReadOnly(False)
            self.f_item_code.setFocus()

    def _populate(self):
        p = self.prod
        def sv(w, key, default=""):
            val = p.get(key, default)
            if val is None:
                val = default
            if isinstance(w, QLineEdit):
                w.setText(str(val))
            elif isinstance(w, QComboBox):
                idx = w.findText(str(val))
                if idx >= 0:
                    w.setCurrentIndex(idx)
                else:
                    w.setEditText(str(val))
            elif isinstance(w, (QSpinBox, QDoubleSpinBox)):
                try:
                    w.setValue(float(val))
                except (ValueError, TypeError):
                    pass
            elif isinstance(w, QCheckBox):
                w.setChecked(bool(val))
            elif isinstance(w, QTextEdit):
                w.setPlainText(str(val))
            elif isinstance(w, QDateEdit):
                try:
                    d = QDate.fromString(str(val), "yyyy-MM-dd")
                    if d.isValid():
                        w.setDate(d)
                except Exception:
                    pass

        sv(self.f_item_code,        "item_code")
        sv(self.f_name,             "name")
        sv(self.f_barcode,          "barcode")
        sv(self.f_hsn,              "hsn_code")
        sv(self.f_category,         "category")
        sv(self.f_sub_cat,          "sub_category")
        sv(self.f_brand,            "brand")
        sv(self.f_manufacturer,     "manufacturer")
        sv(self.f_unit,             "unit")
        sv(self.f_pack_size,        "pack_size", 1)
        sv(self.f_meter,            "meter")
        sv(self.f_desc,             "description")

        sv(self.f_purchase_price,   "purchase_price")
        sv(self.f_selling_price,    "selling_price")
        sv(self.f_wholesale_price,  "wholesale_price")
        sv(self.f_min_selling_price,"min_selling_price")
        sv(self.f_discount_pct,     "discount_pct")
        sv(self.f_tax_inclusive,    "tax_inclusive")
        sv(self.f_gst_rate,         "gst_rate")
        sv(self.f_tax_type,         "tax_type")
        sv(self.f_cess_pct,         "cess_pct")

        sv(self.f_opening_stock,    "opening_stock")
        sv(self.f_reorder_level,    "reorder_level")
        sv(self.f_min_order_qty,    "min_order_qty")
        sv(self.f_max_stock,        "max_stock")
        sv(self.f_allow_neg,        "allow_neg_stock")
        sv(self.f_warehouse,        "warehouse")
        sv(self.f_rack,             "rack_location")
        sv(self.f_track_batch,      "track_batch")
        sv(self.f_track_expiry,     "track_expiry")
        sv(self.f_mfg_date,         "mfg_date")
        sv(self.f_expiry_date,      "expiry_date")
        sv(self.f_expiry_alert,     "expiry_alert_days", 30)
        sv(self.f_returnable,       "is_returnable")

        sv(self.f_supplier_name,    "supplier_name")
        sv(self.f_supplier_code,    "supplier_code")
        sv(self.f_lead_time,        "lead_time_days")
        sv(self.f_last_purchase,    "last_purchase_price")

        sv(self.f_weight,           "weight_kg")
        sv(self.f_length,           "length_cm")
        sv(self.f_width,            "width_cm")
        sv(self.f_height,           "height_cm")
        sv(self.f_has_variants,     "has_variants")
        sv(self.f_variant_type,     "variant_type")
        sv(self.f_status,           "status")
        sv(self.f_notes,            "internal_notes")

        if self.edit_code:
            self.f_item_code.setReadOnly(True)
            self.f_auto_code.setVisible(False)

    def _collect(self) -> dict:
        def gst_val():
            t = self.f_gst_rate.currentText()
            return t.split("%")[0].strip() + "%"

        return {
            "item_code":          self.f_item_code.text().strip(),
            "name":               self.f_name.text().strip(),
            "description":        self.f_desc.toPlainText().strip(),
            "category":           self.f_category.currentText().strip(),
            "sub_category":       self.f_sub_cat.text().strip(),
            "brand":              self.f_brand.text().strip(),
            "manufacturer":       self.f_manufacturer.text().strip(),
            "hsn_code":           self.f_hsn.text().strip(),
            "barcode":            self.f_barcode.text().strip(),
            "unit":               self.f_unit.currentText().strip(),
            "pack_size":          self.f_pack_size.value(),
            "meter":              self.f_meter.text().strip(),
            "purchase_price":     self.f_purchase_price.value(),
            "selling_price":      self.f_selling_price.value(),
            "wholesale_price":    self.f_wholesale_price.value(),
            "min_selling_price":  self.f_min_selling_price.value(),
            "discount_pct":       self.f_discount_pct.value(),
            "tax_inclusive":      int(self.f_tax_inclusive.isChecked()),
            "gst_rate":           gst_val(),
            "tax_type":           self.f_tax_type.currentText(),
            "cess_pct":           self.f_cess_pct.value(),
            "opening_stock":      self.f_opening_stock.value(),
            "stock":              self.f_opening_stock.value(),
            "reorder_level":      self.f_reorder_level.value(),
            "min_order_qty":      self.f_min_order_qty.value(),
            "max_stock":          self.f_max_stock.value(),
            "warehouse":          self.f_warehouse.currentText().strip(),
            "rack_location":      self.f_rack.text().strip(),
            "track_batch":        int(self.f_track_batch.isChecked()),
            "track_expiry":       int(self.f_track_expiry.isChecked()),
            "mfg_date":           self.f_mfg_date.date().toString("yyyy-MM-dd"),
            "expiry_date":        self.f_expiry_date.date().toString("yyyy-MM-dd"),
            "expiry_alert_days":  self.f_expiry_alert.value(),
            "is_returnable":      int(self.f_returnable.isChecked()),
            "allow_neg_stock":    int(self.f_allow_neg.isChecked()),
            "supplier_name":      self.f_supplier_name.currentText().strip(),
            "supplier_code":      self.f_supplier_code.text().strip(),
            "lead_time_days":     self.f_lead_time.value(),
            "last_purchase_price":self.f_last_purchase.value(),
            "weight_kg":          self.f_weight.value(),
            "length_cm":          self.f_length.value(),
            "width_cm":           self.f_width.value(),
            "height_cm":          self.f_height.value(),
            "has_variants":       int(self.f_has_variants.isChecked()),
            "variant_type":       self.f_variant_type.currentText().strip(),
            "internal_notes":     self.f_notes.toPlainText().strip(),
            "status":             self.f_status.currentText(),
        }

    def _save(self):
        data = self._collect()

        if not data["name"]:
            QMessageBox.warning(self, "Validation", "Product name is required.")
            self.tabs.setCurrentIndex(0)
            self.f_name.setFocus()
            return
        if not data["item_code"]:
            QMessageBox.warning(self, "Validation", "Item code is required.")
            self.tabs.setCurrentIndex(0)
            self.f_item_code.setFocus()
            return
        if data["selling_price"] <= 0:
            QMessageBox.warning(self, "Validation", "Selling price must be greater than 0.")
            self.tabs.setCurrentIndex(1)
            self.f_selling_price.setFocus()
            return

        if self.edit_code:
            d = dict(data)
            d.pop("item_code", None)
            update_product(self.db_name, self.edit_code, d)
        else:
            ok = save_product(self.db_name, data)
            if not ok:
                QMessageBox.critical(
                    self, "Error",
                    "Could not save product.\n"
                    "Item code may already exist."
                )
                return

        self.accept()


# ─────────────────────────────────────────────────────────
#  PRODUCT PAGE (main widget)
# ─────────────────────────────────────────────────────────
class ProductPage(QWidget):

    def __init__(self, db_name, company_name="", on_back=None):
        super().__init__()
        self.db_name      = db_name
        self.company_name = company_name
        self.on_back      = on_back

        init_product_table(db_name)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── TOP BAR ─────────────────────────────
        top_bar = QFrame()
        top_bar.setFixedHeight(62)
        top_bar.setStyleSheet(
            f"background: {WHITE}; border-bottom: 1px solid {BORDER};"
        )
        tl = QHBoxLayout(top_bar)
        tl.setContentsMargins(16, 0, 16, 0)

        back_btn = QPushButton("←  Back")
        back_btn.setFixedSize(90, 34)
        back_btn.setStyleSheet(f"""
            QPushButton {{ background:#f0f7ff; color:{PRIMARY};
                border:1px solid #4da3ff; border-radius:6px;
                font-weight:700; font-size:13px; }}
            QPushButton:hover {{ background:#ddeeff; }}
        """)
        back_btn.clicked.connect(lambda: self.on_back() if self.on_back else None)

        center = QLabel(company_name)
        center.setAlignment(Qt.AlignCenter)
        center.setFont(QFont("Segoe UI", 14, QFont.Bold))

        add_btn = QPushButton("＋  Add Product")
        add_btn.setFixedSize(145, 34)
        add_btn.setStyleSheet(f"""
            QPushButton {{ background:{PRIMARY}; color:white;
                border-radius:6px; font-weight:700; font-size:13px;
                border:none; }}
            QPushButton:hover {{ background:#1565c0; }}
        """)
        add_btn.clicked.connect(self.add_product)

        tl.addWidget(back_btn)
        tl.addStretch()
        tl.addWidget(center)
        tl.addStretch()
        tl.addWidget(add_btn)
        layout.addWidget(top_bar)

        # ── CONTENT ─────────────────────────────
        content = QWidget()
        content.setStyleSheet(f"background:{BG_LIGHT};")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(28, 20, 28, 20)
        cl.setSpacing(14)

        title = QLabel("Products")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        cl.addWidget(title)

        # Search bar
        sf = QFrame()
        sf.setFixedHeight(46)
        sf.setStyleSheet(f"""
            QFrame {{ background:white;
                border:1px solid #c0d6ea; border-radius:8px; }}
        """)
        sl = QHBoxLayout(sf)
        sl.setContentsMargins(12, 0, 12, 0)
        sl.setSpacing(8)

        ico = QLabel("🔍")
        ico.setStyleSheet("background:transparent;border:none;font-size:15px;")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by item code or product name…")
        self.search_input.setStyleSheet(
            "border:none;background:transparent;font-size:13px;color:#333;"
        )
        self.search_input.textChanged.connect(self._on_search)

        clr = QPushButton("✕")
        clr.setFixedSize(24, 24)
        clr.setStyleSheet("""
            QPushButton { background:#eee; border-radius:12px;
                color:#666; font-size:11px; border:none; }
            QPushButton:hover { background:#ddd; }
        """)
        clr.clicked.connect(self._clear_search)

        sl.addWidget(ico)
        sl.addWidget(self.search_input)
        sl.addWidget(clr)
        cl.addWidget(sf)

        # Suggestion dropdown
        self.suggest_list = QListWidget()
        self.suggest_list.setFixedHeight(150)
        self.suggest_list.setStyleSheet("""
            QListWidget { background:white; border:1px solid #c0d6ea;
                border-radius:6px; font-size:13px; }
            QListWidget::item { padding:6px 12px; }
            QListWidget::item:hover { background:#eef5ff; }
            QListWidget::item:selected { background:#ddeeff; color:#111; }
        """)
        self.suggest_list.setVisible(False)
        self.suggest_list.itemClicked.connect(self._on_suggestion)
        cl.addWidget(self.suggest_list)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "Item Code", "Product Name", "Category",
            "Unit", "GST", "Price (₹)", "Stock",
            "Reorder", "Status", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(9, QHeaderView.Fixed)
        self.table.setColumnWidth(9, 95)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { background:white; border:1px solid #e0e0e0;
                border-radius:8px; gridline-color:#f0f0f0; font-size:13px; }
            QHeaderView::section { background:#f8fafc; font-weight:700;
                padding:8px; border:none;
                border-bottom:2px solid #e0e8f0; color:#444; }
            QTableWidget::item { padding:6px 8px; }
            QTableWidget::item:selected { background:#eef5ff; color:#111; }
        """)
        cl.addWidget(self.table)
        layout.addWidget(content)

        self._load_table()

    # ── Table loading ────────────────────────
    def _load_table(self, rows=None):
        if rows is None:
            rows = get_all_products(self.db_name)
        self.table.setRowCount(0)
        for rd in rows:
            code, name, cat, unit, _, price, stock, status, hsn, gst = rd
            r = self.table.rowCount()
            self.table.insertRow(r)

            self.table.setItem(r, 0, QTableWidgetItem(str(code or "")))
            self.table.setItem(r, 1, QTableWidgetItem(str(name or "")))
            self.table.setItem(r, 2, QTableWidgetItem(str(cat or "")))
            self.table.setItem(r, 3, QTableWidgetItem(str(unit or "")))

            gst_item = QTableWidgetItem(str(gst or ""))
            gst_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 4, gst_item)

            pi = QTableWidgetItem(f"₹{float(price or 0):,.2f}")
            pi.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(r, 5, pi)

            si = QTableWidgetItem(str(stock or 0))
            si.setTextAlignment(Qt.AlignCenter)

            prod = get_product_full(self.db_name, code)
            reorder = prod.get("reorder_level", 0) if prod else 0
            if stock is not None and reorder and int(stock) <= int(reorder):
                si.setForeground(QBrush(QColor(DANGER)))
                si.setBackground(QBrush(QColor("#fff0f0")))
            self.table.setItem(r, 6, si)

            ri = QTableWidgetItem(str(reorder))
            ri.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 7, ri)

            sti = QTableWidgetItem(str(status or ""))
            sti.setTextAlignment(Qt.AlignCenter)
            if status == "Active":
                sti.setForeground(QBrush(QColor("#1a7fe8")))
                sti.setBackground(QBrush(QColor("#eef5ff")))
            elif status == "Draft":
                sti.setForeground(QBrush(QColor("#e67e00")))
                sti.setBackground(QBrush(QColor("#fff8ee")))
            else:
                sti.setForeground(QBrush(QColor("#888")))
                sti.setBackground(QBrush(QColor("#f5f5f5")))
            self.table.setItem(r, 8, sti)

            # Action buttons
            aw = QWidget()
            al = QHBoxLayout(aw)
            al.setContentsMargins(4, 2, 4, 2)
            al.setSpacing(6)

            eb = QPushButton("📝")
            eb.setFixedSize(28, 28)
            eb.setStyleSheet("""
                QPushButton { background:#eef5ff; color:#1a7fe8;
                    border-radius:5px; border:none; font-size:14px; }
                QPushButton:hover { background:#ddeeff; }
            """)
            eb.clicked.connect(lambda _, c=code: self._edit(c))

            db = QPushButton("🗑️")
            db.setFixedSize(28, 28)
            db.setStyleSheet("""
                QPushButton { background:#fff0f0; color:#e53935;
                    border-radius:5px; border:none; font-size:14px; }
                QPushButton:hover { background:#ffd6d6; }
            """)
            db.clicked.connect(lambda _, c=code: self._confirm_delete(c))

            al.addWidget(eb)
            al.addWidget(db)
            self.table.setCellWidget(r, 9, aw)
            self.table.setRowHeight(r, 42)

    # ── Search ───────────────────────────────
    def _on_search(self, text):
        text = text.strip()
        if not text:
            self.suggest_list.setVisible(False)
            self._load_table()
            return
        suggestions = search_suggestions(self.db_name, text)
        self.suggest_list.clear()
        if suggestions:
            for code, name in suggestions:
                it = QListWidgetItem(f"  {code}  –  {name}")
                it.setData(Qt.UserRole, code)
                self.suggest_list.addItem(it)
            self.suggest_list.setVisible(True)
        else:
            self.suggest_list.setVisible(False)
        self._load_table(search_products(self.db_name, text))

    def _on_suggestion(self, item):
        code = item.data(Qt.UserRole)
        self.search_input.setText(code)
        self.suggest_list.setVisible(False)
        self._load_table(search_products(self.db_name, code))

    def _clear_search(self):
        self.search_input.clear()
        self.suggest_list.setVisible(False)
        self._load_table()

    # ── CRUD ─────────────────────────────────
    def add_product(self):
        dlg = ProductDialog(self.db_name, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._load_table()

    def _edit(self, item_code):
        dlg = ProductDialog(self.db_name, item_code=item_code, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._load_table()

    def _confirm_delete(self, item_code):
        reply = QMessageBox.question(
            self, "Delete Product",
            f"Delete product  '{item_code}' ?\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            delete_product(self.db_name, item_code)
            self._load_table()


# ─────────────────────────────────────────────────────────
#  QUICK TEST
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    DB = "billing_test.db"
    win = ProductPage(DB, company_name="Sri Murugan Traders")
    win.setWindowTitle("Product Manager")
    win.resize(1100, 700)
    win.show()
    sys.exit(app.exec_())