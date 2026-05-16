import sys
import sqlite3

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QMessageBox, QDialog,
    QGridLayout, QComboBox, QCompleter, QAbstractItemView,
    QListWidget, QListWidgetItem
)
from PyQt5.QtGui import QFont, QColor, QBrush, QIcon
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QStringListModel, QTimer


# ──────────────────────────────────────────
#  DB FUNCTIONS
# ──────────────────────────────────────────
def init_product_table(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            item_code   TEXT UNIQUE,
            name        TEXT NOT NULL,
            category    TEXT,
            unit        TEXT,
            meter       TEXT,
            price       REAL,
            stock       INTEGER,
            status      TEXT DEFAULT 'Active'
        )
    """)
    conn.commit()
    conn.close()


def get_all_products(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT item_code, name, category, unit, meter, price, stock, status
        FROM products ORDER BY item_code
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


def search_products(db_name, query):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT item_code, name, category, unit, meter, price, stock, status
        FROM products
        WHERE item_code LIKE ? OR name LIKE ?
        ORDER BY item_code
    """, (f"%{query}%", f"%{query}%"))
    rows = cursor.fetchall()
    conn.close()
    return rows


def search_suggestions(db_name, query):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT item_code, name FROM products
        WHERE item_code LIKE ? OR name LIKE ?
        LIMIT 10
    """, (f"%{query}%", f"%{query}%"))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_next_item_code(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]
    conn.close()
    return f"P{str(count + 1).zfill(5)}"


def save_product(db_name, item_code, name, category, unit, meter, price, stock, status):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO products (item_code, name, category, unit, meter, price, stock, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (item_code, name, category, unit, meter, float(price), int(stock), status))
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        conn.close()


def update_product(db_name, item_code, name, category, unit, meter, price, stock, status):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE products SET name=?, category=?, unit=?, meter=?, price=?, stock=?, status=?
        WHERE item_code=?
    """, (name, category, unit, meter, float(price), int(stock), status, item_code))
    conn.commit()
    conn.close()


def delete_product(db_name, item_code):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE item_code=?", (item_code,))
    conn.commit()
    conn.close()


# ──────────────────────────────────────────
#  ADD / EDIT PRODUCT DIALOG
# ──────────────────────────────────────────
class ProductDialog(QDialog):

    def __init__(self, db_name, product=None, parent=None):
        super().__init__(parent)
        self.db_name = db_name
        self.product = product  # None = Add, tuple = Edit

        title = "Edit Product" if product else "Add Product"
        self.setWindowTitle(title)
        self.setFixedSize(460, 420)

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(14)

        heading = QLabel(f"{'✏️  Edit' if product else '✚  Add'} Product")
        heading.setAlignment(Qt.AlignCenter)
        heading.setStyleSheet("font-size: 15px; font-weight: bold; color: #1a7fe8;")
        layout.addWidget(heading)

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setColumnMinimumWidth(0, 110)
        grid.setColumnMinimumWidth(1, 250)

        self.item_code = QLineEdit()
        self.item_code.setMinimumHeight(32)
        self.item_code.setPlaceholderText("Auto-generated")
        if product:
            self.item_code.setText(product[0])
            self.item_code.setReadOnly(True)
            self.item_code.setStyleSheet("background: #f5f5f5; color: #888;")
        else:
            code = get_next_item_code(db_name)
            self.item_code.setText(code)
            self.item_code.setReadOnly(True)
            self.item_code.setStyleSheet("background: #f5f5f5; color: #888;")

        self.name = QLineEdit()
        self.name.setMinimumHeight(32)
        self.name.setPlaceholderText("Product name")

        self.category = QLineEdit()
        self.category.setMinimumHeight(32)
        self.category.setPlaceholderText("e.g. Mobiles, Grocery")

        self.unit = QLineEdit()
        self.unit.setMinimumHeight(32)
        self.unit.setPlaceholderText("e.g. Nos, Strip, Pack")

        self.meter = QLineEdit()
        self.meter.setMinimumHeight(32)
        self.meter.setPlaceholderText("e.g. Piece(s), 10 Tablets")

        self.price = QLineEdit()
        self.price.setMinimumHeight(32)
        self.price.setPlaceholderText("0.00")

        self.stock = QLineEdit()
        self.stock.setMinimumHeight(32)
        self.stock.setPlaceholderText("0")

        self.status = QComboBox()
        self.status.setMinimumHeight(32)
        self.status.addItems(["Active", "Inactive"])

        # Fill values if editing
        if product:
            self.name.setText(product[1])
            self.category.setText(product[2] or "")
            self.unit.setText(product[3] or "")
            self.meter.setText(product[4] or "")
            self.price.setText(str(product[5]))
            self.stock.setText(str(product[6]))
            idx = self.status.findText(product[7])
            if idx >= 0:
                self.status.setCurrentIndex(idx)

        grid.addWidget(QLabel("Item Code"),  0, 0)
        grid.addWidget(self.item_code,        0, 1)
        grid.addWidget(QLabel("Name *"),     1, 0)
        grid.addWidget(self.name,             1, 1)
        grid.addWidget(QLabel("Category"),   2, 0)
        grid.addWidget(self.category,         2, 1)
        grid.addWidget(QLabel("Unit"),       3, 0)
        grid.addWidget(self.unit,             3, 1)
        grid.addWidget(QLabel("Meter"),      4, 0)
        grid.addWidget(self.meter,            4, 1)
        grid.addWidget(QLabel("Price (₹)"),  5, 0)
        grid.addWidget(self.price,            5, 1)
        grid.addWidget(QLabel("Stock"),      6, 0)
        grid.addWidget(self.stock,            6, 1)
        grid.addWidget(QLabel("Status"),     7, 0)
        grid.addWidget(self.status,           7, 1)

        layout.addLayout(grid)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_save = QPushButton("Save")
        btn_save.setMinimumHeight(36)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #1a7fe8; color: white;
                border-radius: 6px; font-weight: bold; border: none;
            }
            QPushButton:hover { background-color: #1565c0; }
        """)
        btn_save.clicked.connect(self.save)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setMinimumHeight(36)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0; color: #333;
                border-radius: 6px; font-weight: bold; border: none;
            }
            QPushButton:hover { background-color: #e0e0e0; }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

        self.setLayout(layout)

    def save(self):
        name     = self.name.text().strip()
        price    = self.price.text().strip() or "0"
        stock    = self.stock.text().strip() or "0"

        if not name:
            QMessageBox.warning(self, "Error", "Product name is required.")
            return

        try:
            float(price)
            int(stock)
        except ValueError:
            QMessageBox.warning(self, "Error", "Price and Stock must be numbers.")
            return

        if self.product:
            update_product(
                self.db_name,
                self.item_code.text(),
                name,
                self.category.text().strip(),
                self.unit.text().strip(),
                self.meter.text().strip(),
                price, stock,
                self.status.currentText()
            )
        else:
            ok = save_product(
                self.db_name,
                self.item_code.text(),
                name,
                self.category.text().strip(),
                self.unit.text().strip(),
                self.meter.text().strip(),
                price, stock,
                self.status.currentText()
            )
            if not ok:
                QMessageBox.warning(self, "Error", "Could not save product.")
                return

        self.accept()


# ──────────────────────────────────────────
#  PRODUCT PAGE (embedded widget)
# ──────────────────────────────────────────
class ProductPage(QWidget):

    def __init__(self, db_name, company_name="", on_back=None):
        super().__init__()
        self.db_name      = db_name
        self.company_name = company_name
        self.on_back      = on_back   # callback to go back to dashboard

        init_product_table(db_name)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── TOP BAR ──
        top_bar = QFrame()
        top_bar.setFixedHeight(60)
        top_bar.setStyleSheet("background: white; border-bottom: 1px solid #e0e0e0;")

        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 0, 16, 0)

        back_btn = QPushButton("←  Back")
        back_btn.setFixedHeight(34)
        back_btn.setFixedWidth(90)
        back_btn.setStyleSheet("""
            QPushButton {
                background: #f0f7ff; color: #1a7fe8;
                border: 1px solid #4da3ff; border-radius: 6px;
                font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background: #ddeeff; }
        """)
        back_btn.clicked.connect(self._go_back)

        center_label = QLabel(company_name)
        center_label.setAlignment(Qt.AlignCenter)
        center_label.setFont(QFont("Segoe UI", 14, QFont.Bold))

        add_btn = QPushButton("＋  Add Product")
        add_btn.setFixedHeight(34)
        add_btn.setFixedWidth(140)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a7fe8; color: white;
                border-radius: 6px; font-weight: bold;
                font-size: 13px; border: none;
            }
            QPushButton:hover { background-color: #1565c0; }
        """)
        add_btn.clicked.connect(self.add_product)

        top_layout.addWidget(back_btn)
        top_layout.addStretch()
        top_layout.addWidget(center_label)
        top_layout.addStretch()
        top_layout.addWidget(add_btn)

        layout.addWidget(top_bar)

        # ── CONTENT AREA ──
        content = QWidget()
        content.setStyleSheet("background: #f4f7fb;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 24, 30, 24)
        content_layout.setSpacing(16)

        # Title
        title_lbl = QLabel("Products")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        content_layout.addWidget(title_lbl)

        # ── SEARCH BAR ──
        search_frame = QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #c0d6ea;
                border-radius: 8px;
            }
        """)
        search_frame.setFixedHeight(48)

        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(12, 0, 12, 0)
        search_layout.setSpacing(8)

        search_icon = QLabel("🔍︎")
        search_icon.setStyleSheet("background: transparent; border: none; font-size: 16px;")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("item code or Product Name...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: none; background: transparent;
                font-size: 13px; color: #333;
            }
        """)
        self.search_input.textChanged.connect(self.on_search_changed)

        clear_btn = QPushButton("✕")
        clear_btn.setFixedSize(24, 24)
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #eee; border-radius: 12px;
                color: #666; font-size: 11px; border: none;
            }
            QPushButton:hover { background: #ddd; }
        """)
        clear_btn.clicked.connect(self.clear_search)

        search_layout.addWidget(search_icon)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(clear_btn)
        content_layout.addWidget(search_frame)

        # ── SUGGESTION DROPDOWN ──
        self.suggestion_list = QListWidget()
        self.suggestion_list.setFixedHeight(160)
        self.suggestion_list.setStyleSheet("""
            QListWidget {
                background: white;
                border: 1px solid #c0d6ea;
                border-radius: 6px;
                font-size: 13px;
            }
            QListWidget::item { padding: 6px 12px; }
            QListWidget::item:hover { background: #eef5ff; }
            QListWidget::item:selected { background: #ddeeff; color: #111; }
        """)
        self.suggestion_list.setVisible(False)
        self.suggestion_list.itemClicked.connect(self.on_suggestion_clicked)
        content_layout.addWidget(self.suggestion_list)

        # ── TABLE ──
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Item ID (Code)", "Product Name", "Category",
            "Unit", "Meter", "Price (₹)", "Stock", "Status", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Fixed)
        self.table.setColumnWidth(8, 90)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                gridline-color: #f0f0f0;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #f8fafc;
                font-weight: bold;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #e0e8f0;
                color: #444;
            }
            QTableWidget::item { padding: 6px 8px; }
            QTableWidget::item:selected { background: #eef5ff; color: #111; }
        """)

        content_layout.addWidget(self.table)
        layout.addWidget(content)

        self.setLayout(layout)
        self.load_table()

    def _go_back(self):
        if self.on_back:
            self.on_back()

    def load_table(self, rows=None):
        if rows is None:
            rows = get_all_products(self.db_name)
        self.table.setRowCount(0)
        for row_data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)

            code, name, cat, unit, meter, price, stock, status = row_data

            self.table.setItem(row, 0, QTableWidgetItem(str(code)))
            self.table.setItem(row, 1, QTableWidgetItem(str(name)))
            self.table.setItem(row, 2, QTableWidgetItem(str(cat or "")))
            self.table.setItem(row, 3, QTableWidgetItem(str(unit or "")))
            self.table.setItem(row, 4, QTableWidgetItem(str(meter or "")))

            price_item = QTableWidgetItem(f"{float(price):,.2f}")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 5, price_item)

            stock_item = QTableWidgetItem(str(stock))
            stock_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 6, stock_item)

            # Status badge
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)
            if status == "Active":
                status_item.setForeground(QBrush(QColor("#1a7fe8")))
                status_item.setBackground(QBrush(QColor("#eef5ff")))
            else:
                status_item.setForeground(QBrush(QColor("#888")))
                status_item.setBackground(QBrush(QColor("#f5f5f5")))
            self.table.setItem(row, 7, status_item)

            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 2, 4, 2)
            action_layout.setSpacing(6)

            edit_btn = QPushButton("📝")
            edit_btn.setFixedSize(28, 28)
            edit_btn.setStyleSheet("""
                QPushButton {
                    background: #eef5ff; color: #1a7fe8;
                    border-radius: 5px; border: none; font-size: 14px;
                }
                QPushButton:hover { background: #ddeeff; }
            """)
            edit_btn.clicked.connect(lambda _, c=code: self.edit_product(c))

            del_btn = QPushButton("🗑️")
            del_btn.setFixedSize(28, 28)
            del_btn.setStyleSheet("""
                QPushButton {
                    background: #fff0f0; color: #e53935;
                    border-radius: 5px; border: none; font-size: 14px;
                }
                QPushButton:hover { background: #ffd6d6; }
            """)
            del_btn.clicked.connect(lambda _, c=code: self.confirm_delete(c))

            action_layout.addWidget(edit_btn)
            action_layout.addWidget(del_btn)
            self.table.setCellWidget(row, 8, action_widget)

            self.table.setRowHeight(row, 42)

    def on_search_changed(self, text):
        text = text.strip()
        if not text:
            self.suggestion_list.setVisible(False)
            self.load_table()
            return

        suggestions = search_suggestions(self.db_name, text)
        self.suggestion_list.clear()

        if suggestions:
            for code, name in suggestions:
                item = QListWidgetItem(f"  {code} - {name}")
                item.setData(Qt.UserRole, code)
                self.suggestion_list.addItem(item)
            self.suggestion_list.setVisible(True)
        else:
            self.suggestion_list.setVisible(False)

        self.load_table(search_products(self.db_name, text))

    def on_suggestion_clicked(self, item):
        code = item.data(Qt.UserRole)
        self.search_input.setText(code)
        self.suggestion_list.setVisible(False)
        self.load_table(search_products(self.db_name, code))

    def clear_search(self):
        self.search_input.clear()
        self.suggestion_list.setVisible(False)
        self.load_table()

    def add_product(self):
        dlg = ProductDialog(self.db_name, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self.load_table()

    def edit_product(self, item_code):
        rows = search_products(self.db_name, item_code)
        product = next((r for r in rows if r[0] == item_code), None)
        if product:
            dlg = ProductDialog(self.db_name, product=product, parent=self)
            if dlg.exec_() == QDialog.Accepted:
                self.load_table()

    def confirm_delete(self, item_code):
        reply = QMessageBox.question(
            self, "Delete Product",
            f"Delete product '{item_code}'?\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            delete_product(self.db_name, item_code)
            self.load_table()