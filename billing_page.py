import sqlite3
import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QMessageBox, QAbstractItemView,
    QGridLayout, QComboBox, QShortcut, QSizePolicy,
    QDialog, QSpinBox, QDoubleSpinBox
)
from PyQt5.QtGui import QFont, QColor, QBrush, QKeySequence
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QPainter, QTextDocument


# ──────────────────────────────────────────
#  DB FUNCTIONS
# ──────────────────────────────────────────
def init_billing_tables(db_name):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id     TEXT PRIMARY KEY,
            date           TEXT,
            total          REAL,
            discount_amt   REAL,
            discount_pct   REAL,
            sgst           REAL,
            cgst           REAL,
            grand_total    REAL,
            payment_method TEXT DEFAULT 'Cash'
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS invoice_items (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id   TEXT,
            product_code TEXT,
            product_name TEXT,
            price        REAL,
            quantity     INTEGER,
            total        REAL,
            FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id)
        )
    """)
    conn.commit()
    conn.close()


def generate_invoice_id(db_name):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    today = datetime.now().strftime("%Y%m%d")
    c.execute(
        "SELECT COUNT(*) FROM invoices WHERE invoice_id LIKE ?",
        (f"INV{today}%",)
    )
    count = c.fetchone()[0] + 1
    conn.close()
    return f"INV{today}{str(count).zfill(4)}"


def save_invoice(db_name, invoice_id, items, total,
                 discount_amt, discount_pct, sgst, cgst,
                 grand_total, payment_method="Cash"):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
        INSERT INTO invoices
        (invoice_id, date, total, discount_amt, discount_pct,
         sgst, cgst, grand_total, payment_method)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (invoice_id, date, total, discount_amt, discount_pct,
          sgst, cgst, grand_total, payment_method))
    for item in items:
        c.execute("""
            INSERT INTO invoice_items
            (invoice_id, product_code, product_name, price, quantity, total)
            VALUES (?,?,?,?,?,?)
        """, (invoice_id, item["code"], item["name"],
              item["price"], item["qty"], item["total"]))
    conn.commit()
    conn.close()


def get_product_by_code(db_name, code):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("""
        SELECT item_code, name, price, stock FROM products
        WHERE item_code=? AND status='Active'
    """, (code,))
    row = c.fetchone()
    conn.close()
    return row


def search_product_suggestions(db_name, query):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("""
        SELECT item_code, name, price FROM products
        WHERE (item_code LIKE ? OR name LIKE ?) AND status='Active'
        LIMIT 8
    """, (f"%{query}%", f"%{query}%"))
    rows = c.fetchall()
    conn.close()
    return rows


def load_company_info_billing(db_name):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("SELECT logo, company_name, phone, address, gst, footer FROM company_info WHERE id=1")
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "logo": row[0] or "", "company_name": row[1] or "",
            "phone": row[2] or "", "address": row[3] or "",
            "gst": row[4] or "", "footer": row[5] or ""
        }
    return {}


# ──────────────────────────────────────────
#  CASH RETURN POPUP
# ──────────────────────────────────────────
class CashReturnDialog(QDialog):
    def __init__(self, grand_total, parent=None):
        super().__init__(parent)
        self.grand_total = grand_total
        self.setWindowTitle("Cash Received")
        self.setFixedSize(340, 220)

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(14)

        layout.addWidget(self._lbl(f"Grand Total:  ₹ {grand_total:,.2f}", 15, bold=True))

        row = QHBoxLayout()
        row.addWidget(self._lbl("Cash Received: ₹", 13))
        self.cash_input = QLineEdit()
        self.cash_input.setMinimumHeight(34)
        self.cash_input.setPlaceholderText("0.00")
        self.cash_input.textChanged.connect(self._calc)
        row.addWidget(self.cash_input)
        layout.addLayout(row)

        self.return_lbl = QLabel("Return:  ₹ 0.00")
        self.return_lbl.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #1a7fe8; "
            "background: #eef5ff; border-radius: 6px; padding: 6px;"
        )
        self.return_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.return_lbl)

        btn_row = QHBoxLayout()
        ok_btn = QPushButton("✅  Confirm & Save")
        ok_btn.setMinimumHeight(36)
        ok_btn.setStyleSheet(
            "background:#1a7fe8;color:white;border-radius:6px;font-weight:bold;border:none;"
        )
        ok_btn.clicked.connect(self.accept)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(36)
        cancel_btn.setStyleSheet(
            "background:#eee;color:#333;border-radius:6px;font-weight:bold;border:none;"
        )
        cancel_btn.clicked.connect(self.reject)

        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        self.setLayout(layout)
        self.cash_input.setFocus()

    def _lbl(self, text, size=13, bold=False):
        l = QLabel(text)
        weight = QFont.Bold if bold else QFont.Normal
        l.setFont(QFont("Segoe UI", size, weight))
        return l

    def _calc(self):
        try:
            cash = float(self.cash_input.text())
            ret  = cash - self.grand_total
            color = "#1a7fe8" if ret >= 0 else "#e53935"
            self.return_lbl.setText(f"Return:  ₹ {ret:,.2f}")
            self.return_lbl.setStyleSheet(
                f"font-size:16px;font-weight:bold;color:{color};"
                "background:#eef5ff;border-radius:6px;padding:6px;"
            )
        except ValueError:
            self.return_lbl.setText("Return:  ₹ 0.00")


# ──────────────────────────────────────────
#  BILLING PAGE
# ──────────────────────────────────────────
class BillingPage(QWidget):

    def __init__(self, db_name, company_name="", on_back=None):
        super().__init__()
        self.db_name      = db_name
        self.company_name = company_name
        self.on_back      = on_back
        self.items        = []   # list of dicts, never touches DB until save

        init_billing_tables(db_name)

        self.invoice_id = generate_invoice_id(db_name)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_topbar())
        layout.addWidget(self._build_body())
        layout.addWidget(self._build_bottom())

        self.setLayout(layout)
        self.setStyleSheet("background:#f4f7fb;")

        # F11 shortcut → Save & Print
        shortcut = QShortcut(QKeySequence("F11"), self)
        shortcut.activated.connect(self._checkout)

        # Add first empty row
        self._add_row()

    # ──────────────────────────────────────
    #  TOP BAR
    # ──────────────────────────────────────
    def _build_topbar(self):
        bar = QFrame()
        bar.setFixedHeight(60)
        bar.setStyleSheet("background:white; border-bottom:1px solid #e0e0e0;")

        lay = QHBoxLayout(bar)
        lay.setContentsMargins(16, 0, 16, 0)

        back_btn = QPushButton("←  Back")
        back_btn.setFixedSize(90, 34)
        back_btn.setStyleSheet(
            "background:#f0f7ff;color:#1a7fe8;border:1px solid #4da3ff;"
            "border-radius:6px;font-weight:bold;font-size:13px;"
        )
        back_btn.clicked.connect(self._go_back)

        center = QLabel(self.company_name)
        center.setAlignment(Qt.AlignCenter)
        center.setFont(QFont("Segoe UI", 14, QFont.Bold))

        self.inv_lbl = QLabel(f"Invoice: {self.invoice_id}")
        self.inv_lbl.setStyleSheet("font-size:12px; color:#888;")

        save_btn = QPushButton("💾  Save & Print   [F11]")
        save_btn.setFixedHeight(34)
        save_btn.setStyleSheet(
            "background:#1a7fe8;color:white;border-radius:6px;"
            "font-weight:bold;font-size:13px;border:none;padding:0 16px;"
        )
        save_btn.clicked.connect(self._checkout)

        lay.addWidget(back_btn)
        lay.addStretch()
        lay.addWidget(center)
        lay.addStretch()
        lay.addWidget(self.inv_lbl)
        lay.addSpacing(16)
        lay.addWidget(save_btn)

        return bar

    # ──────────────────────────────────────
    #  BODY — search bar + table
    # ──────────────────────────────────────
    def _build_body(self):
        body = QWidget()
        body.setStyleSheet("background:#f4f7fb;")
        lay = QVBoxLayout(body)
        lay.setContentsMargins(24, 16, 24, 8)
        lay.setSpacing(10)

        # Date + Invoice row
        info_row = QHBoxLayout()
        date_str = datetime.now().strftime("%d-%m-%Y  %H:%M")
        info_row.addWidget(QLabel(f"📅  {date_str}"))
        info_row.addStretch()
        lay.addLayout(info_row)

        # Search / barcode input
        search_frame = QFrame()
        search_frame.setFixedHeight(44)
        search_frame.setStyleSheet(
            "background:white;border:1px solid #c0d6ea;border-radius:8px;"
        )
        sf_lay = QHBoxLayout(search_frame)
        sf_lay.setContentsMargins(12, 0, 12, 0)

        lbl = QLabel("🔍")
        lbl.setStyleSheet("background:transparent;border:none;font-size:16px;")

        self.scan_input = QLineEdit()
        self.scan_input.setPlaceholderText(
            "Scan barcode or type Item Code / Product Name..."
        )
        self.scan_input.setStyleSheet(
            "border:none;background:transparent;font-size:13px;"
        )
        self.scan_input.returnPressed.connect(self._on_scan)
        self.scan_input.textChanged.connect(self._on_type)

        sf_lay.addWidget(lbl)
        sf_lay.addWidget(self.scan_input)
        lay.addWidget(search_frame)

        # Suggestion dropdown
        self.suggest_frame = QFrame()
        self.suggest_frame.setStyleSheet(
            "background:white;border:1px solid #c0d6ea;border-radius:6px;"
        )
        self.suggest_frame.setVisible(False)
        sug_lay = QVBoxLayout(self.suggest_frame)
        sug_lay.setContentsMargins(0, 4, 0, 4)
        sug_lay.setSpacing(0)
        self.suggest_btns = []
        for _ in range(8):
            b = QPushButton()
            b.setStyleSheet(
                "text-align:left;padding:7px 16px;border:none;"
                "background:white;font-size:13px;"
            )
            b.setVisible(False)
            b.setFixedHeight(34)
            b.setCursor(Qt.PointingHandCursor)
            sug_lay.addWidget(b)
            self.suggest_btns.append(b)
        lay.addWidget(self.suggest_frame)

        # TABLE
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "S.No", "Item Code", "Product Name", "Price (₹)", "Qty", "Total (₹)", ""
        ])
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Fixed)
        hdr.setSectionResizeMode(1, QHeaderView.Fixed)
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.Fixed)
        hdr.setSectionResizeMode(4, QHeaderView.Fixed)
        hdr.setSectionResizeMode(5, QHeaderView.Fixed)
        hdr.setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 55)
        self.table.setColumnWidth(1, 110)
        self.table.setColumnWidth(3, 110)
        self.table.setColumnWidth(4, 70)
        self.table.setColumnWidth(5, 120)
        self.table.setColumnWidth(6, 40)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background:white;border:1px solid #e0e0e0;
                border-radius:8px;font-size:13px;gridline-color:#f0f0f0;
            }
            QHeaderView::section {
                background:#f8fafc;font-weight:bold;padding:8px;
                border:none;border-bottom:2px solid #e0e8f0;color:#444;
            }
            QTableWidget::item { padding:4px 6px; }
            QTableWidget::item:selected { background:#eef5ff;color:#111; }
        """)
        self.table.cellChanged.connect(self._on_cell_changed)
        lay.addWidget(self.table)

        return body

    # ──────────────────────────────────────
    #  BOTTOM TOTALS FRAME
    # ──────────────────────────────────────
    def _build_bottom(self):
        bot = QFrame()
        bot.setFixedHeight(160)
        bot.setStyleSheet(
            "background:white;border-top:2px solid #e0e8f0;border-radius:0px;"
        )

        lay = QHBoxLayout(bot)
        lay.setContentsMargins(30, 14, 30, 14)
        lay.setSpacing(30)

        # LEFT — discount fields
        left = QGridLayout()
        left.setSpacing(8)
        left.setColumnMinimumWidth(0, 130)
        left.setColumnMinimumWidth(1, 120)

        self.disc_amt = QLineEdit("0")
        self.disc_amt.setFixedHeight(30)
        self.disc_amt.setPlaceholderText("₹ 0.00")
        self.disc_amt.textChanged.connect(self._on_disc_amt_changed)

        self.disc_pct = QLineEdit("0")
        self.disc_pct.setFixedHeight(30)
        self.disc_pct.setPlaceholderText("0 %")
        self.disc_pct.textChanged.connect(self._on_disc_pct_changed)

        left.addWidget(QLabel("Discount (₹):"),   0, 0)
        left.addWidget(self.disc_amt,               0, 1)
        left.addWidget(QLabel("Discount (%):"),   1, 0)
        left.addWidget(self.disc_pct,               1, 1)
        left.addWidget(QLabel("SGST (2.5%):"),    2, 0)
        self.sgst_lbl = QLabel("₹ 0.00")
        left.addWidget(self.sgst_lbl,               2, 1)
        left.addWidget(QLabel("CGST (2.5%):"),    3, 0)
        self.cgst_lbl = QLabel("₹ 0.00")
        left.addWidget(self.cgst_lbl,               3, 1)

        lay.addLayout(left)
        lay.addStretch()

        # RIGHT — totals
        right = QVBoxLayout()
        right.setSpacing(6)

        sub_row = QHBoxLayout()
        sub_row.addWidget(QLabel("Sub Total:"))
        sub_row.addStretch()
        self.subtotal_lbl = QLabel("₹ 0.00")
        self.subtotal_lbl.setStyleSheet("font-size:14px; font-weight:bold;")
        sub_row.addWidget(self.subtotal_lbl)
        right.addLayout(sub_row)

        # Grand total — large
        grand_row = QHBoxLayout()
        grand_lbl = QLabel("Grand Total:")
        grand_lbl.setFont(QFont("Segoe UI", 18, QFont.Bold))
        grand_row.addWidget(grand_lbl)
        grand_row.addStretch()
        self.grand_lbl = QLabel("₹ 0.00")
        self.grand_lbl.setFont(QFont("Segoe UI", 22, QFont.Bold))
        self.grand_lbl.setStyleSheet("color:#1a7fe8;")
        grand_row.addWidget(self.grand_lbl)
        right.addLayout(grand_row)

        lay.addLayout(right)
        return bot

    # ──────────────────────────────────────
    #  TABLE ROW MANAGEMENT
    # ──────────────────────────────────────
    def _add_row(self, code="", name="", price=0.0, qty=1):
        self.table.blockSignals(True)
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setRowHeight(row, 40)

        # S.No (read-only)
        sno = QTableWidgetItem(str(row + 1))
        sno.setFlags(Qt.ItemIsEnabled)
        sno.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 0, sno)

        # Item code
        code_item = QTableWidgetItem(code)
        code_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 1, code_item)

        # Name
        self.table.setItem(row, 2, QTableWidgetItem(name))

        # Price
        price_item = QTableWidgetItem(f"{price:.2f}" if price else "")
        price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row, 3, price_item)

        # Qty
        qty_item = QTableWidgetItem(str(qty) if code else "")
        qty_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 4, qty_item)

        # Total (read-only)
        total = price * qty if price else 0
        total_item = QTableWidgetItem(f"{total:.2f}" if total else "")
        total_item.setFlags(Qt.ItemIsEnabled)
        total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row, 5, total_item)

        # Delete btn
        del_btn = QPushButton("🗑")
        del_btn.setFixedSize(30, 28)
        del_btn.setStyleSheet(
            "background:#fff0f0;color:#e53935;border-radius:5px;border:none;"
        )
        del_btn.clicked.connect(lambda _, r=row: self._delete_row(r))
        self.table.setCellWidget(row, 6, del_btn)

        self.table.blockSignals(False)

        if code:
            self._recalc()

    def _delete_row(self, row):
        if self.table.rowCount() <= 1:
            # clear instead of delete last row
            self.table.blockSignals(True)
            for col in range(1, 6):
                item = self.table.item(row, col)
                if item:
                    item.setText("")
            self.table.blockSignals(False)
            self._recalc()
            return
        self.table.removeRow(row)
        self._renumber_rows()
        self._recalc()

    def _renumber_rows(self):
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item:
                item.setText(str(r + 1))
            # rewire delete buttons
            del_btn = self.table.cellWidget(r, 6)
            if del_btn:
                try:
                    del_btn.clicked.disconnect()
                except Exception:
                    pass
                del_btn.clicked.connect(lambda _, row=r: self._delete_row(row))

    # ──────────────────────────────────────
    #  SCAN / SEARCH
    # ──────────────────────────────────────
    def _on_scan(self):
        text = self.scan_input.text().strip()
        if not text:
            return
        self._hide_suggestions()

        # Exact code match — barcode scanner
        product = get_product_by_code(self.db_name, text)
        if product:
            self._add_product_to_table(product[0], product[1], product[2])
            self.scan_input.clear()
            return

        # Partial search — manual typing
        results = search_product_suggestions(self.db_name, text)
        if len(results) == 1:
            p = results[0]
            self._add_product_to_table(p[0], p[1], p[2])
            self.scan_input.clear()
        elif results:
            self._show_suggestions(results)
        else:
            QMessageBox.warning(self, "Not Found", f"No product found for '{text}'")
            self.scan_input.clear()


    def _on_type(self, text):
        if not text.strip():
            self._hide_suggestions()
            return

        # Use a small delay — barcode scanner types full code in <50ms
        # so timer prevents suggestion popup during scan
        if hasattr(self, '_scan_timer'):
            self._scan_timer.stop()

        self._scan_timer = QTimer()
        self._scan_timer.setSingleShot(True)
        self._scan_timer.timeout.connect(lambda: self._delayed_suggest(text))
        self._scan_timer.start(80)   # 80ms delay


    def _delayed_suggest(self, text):
        # If text changed again before timer fired, skip
        current = self.scan_input.text().strip()
        if current != text:
            return

        # Try exact match silently first
        product = get_product_by_code(self.db_name, text)
        if product:
            # Exact match found — auto enter without pressing Enter
            self._add_product_to_table(product[0], product[1], product[2])
            self.scan_input.clear()
            self._hide_suggestions()
            return

        # Show suggestions for manual typing
        results = search_product_suggestions(self.db_name, text)
        if results:
            self._show_suggestions(results)
        else:
            self._hide_suggestions()

    def _show_suggestions(self, results):
        for i, btn in enumerate(self.suggest_btns):
            if i < len(results):
                code, name, price = results[i]
                btn.setText(f"  {code}  —  {name}  (₹{price:,.2f})")
                btn.setVisible(True)
                try:
                    btn.clicked.disconnect()
                except Exception:
                    pass
                btn.clicked.connect(
                    lambda _, c=code, n=name, p=price: self._pick_suggestion(c, n, p)
                )
            else:
                btn.setVisible(False)
        self.suggest_frame.setVisible(True)

    def _hide_suggestions(self):
        self.suggest_frame.setVisible(False)
        for btn in self.suggest_btns:
            btn.setVisible(False)

    def _pick_suggestion(self, code, name, price):
        self._add_product_to_table(code, name, price)
        self.scan_input.clear()
        self._hide_suggestions()

    def _add_product_to_table(self, code, name, price):
        # Check if product already in table — increment qty
        for r in range(self.table.rowCount()):
            code_item = self.table.item(r, 1)
            if code_item and code_item.text() == code:
                qty_item = self.table.item(r, 4)
                qty = int(qty_item.text() or "1") + 1
                self.table.blockSignals(True)
                qty_item.setText(str(qty))
                total = float(self.table.item(r, 3).text() or 0) * qty
                self.table.item(r, 5).setText(f"{total:.2f}")
                self.table.blockSignals(False)
                self._recalc()
                return

        # Fill last empty row or add new row
        last = self.table.rowCount() - 1
        code_item = self.table.item(last, 1)
        if code_item and code_item.text().strip() == "":
            # fill empty row
            self.table.blockSignals(True)
            self.table.item(last, 1).setText(code)
            self.table.item(last, 2).setText(name)
            price_item = self.table.item(last, 3)
            price_item.setText(f"{price:.2f}")
            qty_item = self.table.item(last, 4)
            qty_item.setText("1")
            total_item = self.table.item(last, 5)
            total_item.setText(f"{price:.2f}")
            self.table.blockSignals(False)
        else:
            self._add_row(code, name, price, 1)

        # Always add a new empty row at bottom
        self._add_row()
        self._recalc()

    # ──────────────────────────────────────
    #  CELL EDIT — live recalc
    # ──────────────────────────────────────
    def _on_cell_changed(self, row, col):
        if col not in (3, 4):   # only price or qty
            return
        self.table.blockSignals(True)
        try:
            price = float(self.table.item(row, 3).text() or 0)
            qty   = int(self.table.item(row, 4).text() or 1)
            total = price * qty
            self.table.item(row, 5).setText(f"{total:.2f}")
        except (ValueError, AttributeError):
            pass
        self.table.blockSignals(False)
        self._recalc()

    # ──────────────────────────────────────
    #  TOTALS CALCULATION
    # ──────────────────────────────────────
    def _recalc(self):
        subtotal = 0.0
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 5)
            if item and item.text():
                try:
                    subtotal += float(item.text())
                except ValueError:
                    pass

        # Discount
        try:
            disc_amt = float(self.disc_amt.text() or 0)
        except ValueError:
            disc_amt = 0.0
        try:
            disc_pct = float(self.disc_pct.text() or 0)
        except ValueError:
            disc_pct = 0.0

        after_disc = subtotal - disc_amt - (subtotal * disc_pct / 100)
        after_disc = max(after_disc, 0)

        sgst = after_disc * 0.025
        cgst = after_disc * 0.025
        grand = after_disc + sgst + cgst

        self.subtotal_lbl.setText(f"₹ {subtotal:,.2f}")
        self.sgst_lbl.setText(f"₹ {sgst:,.2f}")
        self.cgst_lbl.setText(f"₹ {cgst:,.2f}")
        self.grand_lbl.setText(f"₹ {grand:,.2f}")

        self._subtotal  = subtotal
        self._disc_amt  = disc_amt
        self._disc_pct  = disc_pct
        self._sgst      = sgst
        self._cgst      = cgst
        self._grand     = grand

    def _on_disc_amt_changed(self):
        self._recalc()

    def _on_disc_pct_changed(self):
        self._recalc()

    # ──────────────────────────────────────
    #  COLLECT ITEMS
    # ──────────────────────────────────────
    def _collect_items(self):
        items = []
        for r in range(self.table.rowCount()):
            code = (self.table.item(r, 1).text() or "").strip()
            name = (self.table.item(r, 2).text() or "").strip()
            if not name:
                continue
            try:
                price = float(self.table.item(r, 3).text() or 0)
                qty   = int(self.table.item(r, 4).text() or 1)
                total = float(self.table.item(r, 5).text() or 0)
            except ValueError:
                continue
            items.append({
                "code": code, "name": name,
                "price": price, "qty": qty, "total": total
            })
        return items

    # ──────────────────────────────────────
    #  CHECKOUT — Save & Print
    # ──────────────────────────────────────
    def _checkout(self):
        items = self._collect_items()
        if not items:
            QMessageBox.warning(self, "Empty", "No items in the bill.")
            return

        self._recalc()

        dlg = CashReturnDialog(self._grand, parent=self)
        if dlg.exec_() != QDialog.Accepted:
            return

        # Save to DB only now
        save_invoice(
            self.db_name,
            self.invoice_id,
            items,
            self._subtotal,
            self._disc_amt,
            self._disc_pct,
            self._sgst,
            self._cgst,
            self._grand
        )

        self._print_invoice(items)
        self._new_bill()

    # ──────────────────────────────────────
    #  PRINT
    # ──────────────────────────────────────
    def _print_invoice(self, items):
        company = load_company_info_billing(self.db_name)
        date_str = datetime.now().strftime("%d-%m-%Y %H:%M")

        rows_html = ""
        for i, item in enumerate(items, 1):
            rows_html += f"""
            <tr>
                <td align='center'>{i}</td>
                <td>{item['name']}</td>
                <td align='right'>₹ {item['price']:,.2f}</td>
                <td align='center'>{item['qty']}</td>
                <td align='right'>₹ {item['total']:,.2f}</td>
            </tr>"""

        html = f"""
        <html><body style='font-family:Arial;font-size:12px;'>
        <h2 style='text-align:center;margin:0'>{company.get('company_name','')}</h2>
        <p style='text-align:center;margin:2px'>{company.get('address','')}</p>
        <p style='text-align:center;margin:2px'>Ph: {company.get('phone','')} | GST: {company.get('gst','')}</p>
        <hr/>
        <p><b>Invoice:</b> {self.invoice_id} &nbsp;&nbsp; <b>Date:</b> {date_str}</p>
        <table width='100%' border='1' cellspacing='0' cellpadding='4'
               style='border-collapse:collapse;'>
            <tr style='background:#eef5ff;'>
                <th>S.No</th><th>Product</th><th>Price</th><th>Qty</th><th>Total</th>
            </tr>
            {rows_html}
        </table>
        <br/>
        <table width='100%'>
            <tr><td>Sub Total</td><td align='right'>₹ {self._subtotal:,.2f}</td></tr>
            <tr><td>Discount (₹)</td><td align='right'>- ₹ {self._disc_amt:,.2f}</td></tr>
            <tr><td>Discount (%)</td><td align='right'>{self._disc_pct}%</td></tr>
            <tr><td>SGST (2.5%)</td><td align='right'>₹ {self._sgst:,.2f}</td></tr>
            <tr><td>CGST (2.5%)</td><td align='right'>₹ {self._cgst:,.2f}</td></tr>
            <tr><td><b style='font-size:14px'>Grand Total</b></td>
                <td align='right'><b style='font-size:14px'>₹ {self._grand:,.2f}</b></td></tr>
        </table>
        <hr/>
        <p style='text-align:center'>{company.get('footer','')}</p>
        </body></html>"""

        printer = QPrinter(QPrinter.HighResolution)
        dlg = QPrintDialog(printer, self)
        if dlg.exec_() == QPrintDialog.Accepted:
            doc = QTextDocument()
            doc.setHtml(html)
            doc.print_(printer)

    # ──────────────────────────────────────
    #  NEW BILL
    # ──────────────────────────────────────
    def _new_bill(self):
        self.table.setRowCount(0)
        self.disc_amt.setText("0")
        self.disc_pct.setText("0")
        self.invoice_id = generate_invoice_id(self.db_name)
        self.inv_lbl.setText(f"Invoice: {self.invoice_id}")
        self._recalc()
        self._add_row()

    # ──────────────────────────────────────
    #  BACK
    # ──────────────────────────────────────
    def _go_back(self):
        if self.on_back:
            self.on_back()