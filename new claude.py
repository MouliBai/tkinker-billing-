import sys
import os
import glob
import sqlite3
import random
import string
import pyotp
import qrcode

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel,
    QLineEdit, QGridLayout, QMessageBox, QInputDialog,
    QVBoxLayout, QHBoxLayout, QFrame, QComboBox,
    QCheckBox, QTextEdit, QFileDialog
)

from PyQt5.QtGui import QPixmap, QFont, QIcon
from PyQt5.QtCore import Qt

MASTER_SECRET = "KRSXG5DSNFXGOIDB"

# ──────────────────────────────────────────
#  DATABASE
# ──────────────────────────────────────────
def init_db(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            username       TEXT UNIQUE,
            password       TEXT,
            role           TEXT,
            otp_secret     TEXT,
            recovery_codes TEXT
        )
    """)
    conn.commit()
    conn.close()
    init_company_table(db_name)

def has_users(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

# ──────────────────────────────────────────
#  COMPANY INFO TABLE
# ──────────────────────────────────────────
def init_company_table(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS company_info (
            id           INTEGER PRIMARY KEY,
            logo         BLOB,
            company_name TEXT,
            phone        TEXT,
            address      TEXT,
            gst          TEXT,
            footer       TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_company_info(db_name, logo_path, company_name, phone, address, gst, footer):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    logo_data = None
    if logo_path and os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_data = f.read()   # ✅ ORIGINAL IMAGE STORED

    cursor.execute("SELECT id FROM company_info WHERE id=1")
    exists = cursor.fetchone()

    if exists:
        cursor.execute("""
            UPDATE company_info
            SET logo=?, company_name=?, phone=?, address=?, gst=?, footer=?
            WHERE id=1
        """, (logo_data, company_name, phone, address, gst, footer))
    else:
        cursor.execute("""
            INSERT INTO company_info (id, logo, company_name, phone, address, gst, footer)
            VALUES (1, ?, ?, ?, ?, ?, ?)
        """, (logo_data, company_name, phone, address, gst, footer))

    conn.commit()
    conn.close()

def load_company_info(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT logo, company_name, phone, address, gst, footer
        FROM company_info WHERE id=1
    """)
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {}

    logo_blob = row[0]

    pixmap = QPixmap()
    pixmap = QPixmap()

    if logo_blob:
        # ✅ Case 1: OLD DATA (string path)
        if isinstance(logo_blob, str):
            if os.path.exists(logo_blob):
                pixmap.load(logo_blob)

        # ✅ Case 2: NEW DATA (BLOB)
        elif isinstance(logo_blob, (bytes, bytearray)):
            pixmap.loadFromData(logo_blob)

    return {
        "logo"         : pixmap,
        "company_name" : row[1] or "",
        "phone"        : row[2] or "",
        "address"      : row[3] or "",
        "gst"          : row[4] or "",
        "footer"       : row[5] or ""
    }
# ──────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────
def generate_recovery_codes():
    return [
        ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        for _ in range(5)
    ]

def generate_qr(secret, username):
    uri = pyotp.TOTP(secret).provisioning_uri(
        name=username,
        issuer_name="EvoAura"
    )
    img = qrcode.make(uri)
    path = f"{username}_qr.png"
    img.save(path)
    return path

# ──────────────────────────────────────────
#  MASTER CODE
# ──────────────────────────────────────────
def verify_master_code(code):
    return pyotp.TOTP(MASTER_SECRET).verify(code)

# ──────────────────────────────────────────
#  USER FUNCTIONS
# ──────────────────────────────────────────
def create_user(db_name, username, password, role="user"):
    user_secret    = pyotp.random_base32()
    recovery_codes = generate_recovery_codes()
    qr_path        = generate_qr(user_secret, username)

    conn   = sqlite3.connect(db_name)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users VALUES (NULL, ?, ?, ?, ?, ?)",
            (username, password, role, user_secret, ",".join(recovery_codes))
        )
        conn.commit()
        return {
            "success"        : True,
            "secret"         : user_secret,
            "recovery_codes" : recovery_codes,
            "qr_path"        : qr_path
        }
    except Exception:
        return {"success": False, "message": "Username already exists"}
    finally:
        conn.close()

def login_user(db_name, username, password):
    conn   = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT password, otp_secret, role, recovery_codes FROM users WHERE username=?",
        (username,)
    )
    data = cursor.fetchone()
    conn.close()

    if not data:
        return {"success": False, "message": "User not found"}

    db_pass, secret, role, recovery_codes = data

    if password != db_pass:
        return {"success": False, "message": "Wrong password"}

    return {
        "success"        : True,
        "secret"         : secret,
        "role"           : role,
        "recovery_codes" : recovery_codes.split(",") if recovery_codes else []
    }

def verify_otp(secret, otp):
    return pyotp.TOTP(secret).verify(otp)

def get_all_usernames(db_name):
    conn   = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users ORDER BY username")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

# ──────────────────────────────────────────
#  QR DISPLAY
# ──────────────────────────────────────────
class QRDisplay(QWidget):

    def __init__(self, secret, qr_path, recovery_codes):
        super().__init__()

        self.secret = secret
        self.recovery_codes = recovery_codes

        self.setWindowTitle("Setup 2FA")
        self.setFixedSize(420, 560)

        layout = QVBoxLayout()
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(12)

        # ── TITLE ──
        title = QLabel("📱  Scan QR in Authenticator App")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #1a7fe8;")
        layout.addWidget(title)

        # ── QR IMAGE ──
        qr_label = QLabel()
        pixmap = QPixmap(qr_path).scaled(
            200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        qr_label.setPixmap(pixmap)
        qr_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(qr_label)

        # ── SECRET ──
        lbl_s = QLabel(f"🔑  Secret Key:\n{secret}")
        lbl_s.setWordWrap(True)
        lbl_s.setStyleSheet(
            "font-size: 12px; background:#f0f7ff; padding:8px; border-radius:5px;"
        )
        layout.addWidget(lbl_s)

        # ── RECOVERY CODES ──
        self.lbl_r = QLabel(
            "🛡  Recovery Codes (save these!):\n" + "\n".join(recovery_codes)
        )
        self.lbl_r.setWordWrap(True)
        self.lbl_r.setStyleSheet(
            "font-size: 12px; background:#fff7e6; padding:8px; border-radius:5px;"
        )
        layout.addWidget(self.lbl_r)

        # ── BUTTON ROW ──
        btn_row = QHBoxLayout()

        copy_btn = QPushButton("📋 Copy Codes")
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.setMinimumHeight(34)
        copy_btn.clicked.connect(self.copy_codes)

        done_btn = QPushButton("✅ Done")
        done_btn.setMinimumHeight(34)
        done_btn.clicked.connect(self.close)

        btn_row.addWidget(copy_btn)
        btn_row.addWidget(done_btn)

        layout.addLayout(btn_row)

        self.setLayout(layout)

    # ─────────────────────────────
    # COPY TO CLIPBOARD
    # ─────────────────────────────
    def copy_codes(self):
        clipboard = QApplication.clipboard()
        text = "\n".join(self.recovery_codes)
        clipboard.setText(text)

        QMessageBox.information(
            self,
            "Copied",
            "Recovery codes copied to clipboard ✅"
        )

# ──────────────────────────────────────────
#  STEP 1 — ASK DB NAME
# ──────────────────────────────────────────
class AskDBName(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Evo Aura — First Setup")
        self.setFixedSize(420, 230)

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(16)

        title = QLabel("🏢  Enter Company Name")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a7fe8;")
        layout.addWidget(title)

        sub = QLabel("This will be used as your company name.")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("font-size: 12px; color: #777;")
        layout.addWidget(sub)

        self.db_input = QLineEdit()
        self.db_input.setPlaceholderText("e.g.  my_shop   (no spaces needed)")
        self.db_input.setMinimumHeight(36)
        self.db_input.returnPressed.connect(self.go_next)
        layout.addWidget(self.db_input)

        btn = QPushButton("Next  →")
        btn.setMinimumHeight(38)
        btn.clicked.connect(self.go_next)
        layout.addWidget(btn)

        self.setLayout(layout)

    def go_next(self):
        name = self.db_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Error", "Please enter a Company name.")
            return

        name = name.replace(" ", "_")
        if not name.endswith(".db"):
            name += ".db"

        if os.path.exists(name):
            QMessageBox.warning(
                self, "Already Exists",
                f"'{name}' already exists.\nPlease choose a different name."
            )
            return

        self.auth = StartupAuth(name)
        self.auth.show()
        self.close()

# ──────────────────────────────────────────
#  STEP 2 — MASTER CODE VERIFICATION
# ──────────────────────────────────────────
class StartupAuth(QWidget):

    def __init__(self, db_name):
        super().__init__()
        self.db_name = db_name

        self.setWindowTitle("Security Verification")
        self.setFixedSize(420, 240)
        

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(16)

        title = QLabel("🔐  Enter Master Setup Code")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a7fe8;")
        layout.addWidget(title)

        sub = QLabel(f"Database will be created as:  <b>{db_name}</b>")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("font-size: 12px; color: #555;")
        sub.setTextFormat(Qt.RichText)
        layout.addWidget(sub)

        self.otp_input = QLineEdit()
        self.otp_input.setPlaceholderText("Enter 6-digit TOTP code")
        self.otp_input.setEchoMode(QLineEdit.Password)
        self.otp_input.setMinimumHeight(36)
        self.otp_input.returnPressed.connect(self.verify)
        layout.addWidget(self.otp_input)

        btn = QPushButton("Verify & Create Database")
        btn.setMinimumHeight(38)
        btn.clicked.connect(self.verify)
        layout.addWidget(btn)

        self.setLayout(layout)

    def verify(self):
        code = self.otp_input.text().strip()

        if not verify_master_code(code):
            QMessageBox.warning(self, "Error", "Invalid Master Code ❌\nPlease try again.")
            self.otp_input.clear()
            return

        init_db(self.db_name)

        # Save company name as default in DB
        company_display_name = self.db_name.replace(".db", "").replace("_", " ").title()
        save_company_info(self.db_name, "", company_display_name, "", "", "", "")

        QMessageBox.information(
            self, "Database Created",
            f"✅  '{self.db_name}' created successfully!\nNow create the first user."
        )

        self.company_form = CompanySettings(self.db_name)
        self.company_form.show()
        self.company_form.destroyed.connect(self._open_signup)
        self.close()
    def _open_signup(self):
            self.signup = SignupForm(self.db_name)
            self.signup.show()
    

# ──────────────────────────────────────────
#  SIGNUP
# ──────────────────────────────────────────
class SignupForm(QWidget):

    def __init__(self, db_name):
        super().__init__()
        self.db_name = db_name

        self.setWindowTitle("Create User")
        self.setFixedSize(420, 390)

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 25, 40, 25)
        layout.setSpacing(14)

        title = QLabel("👤  Create New User")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a7fe8;")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setColumnMinimumWidth(0, 110)
        grid.setColumnMinimumWidth(1, 210)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Enter username")
        self.username.setMinimumHeight(34)

        self.password = QLineEdit()
        self.password.setPlaceholderText("Enter password")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setMinimumHeight(34)

        self.confirm_password = QLineEdit()
        self.confirm_password.setPlaceholderText("Confirm password")
        self.confirm_password.setEchoMode(QLineEdit.Password)
        self.confirm_password.setMinimumHeight(34)

        self.show_pass = QCheckBox("Show Password")
        self.show_pass.stateChanged.connect(self.toggle_password)

        self.master = QLineEdit()
        self.master.setPlaceholderText("6-digit TOTP code")
        self.master.setEchoMode(QLineEdit.Password)
        self.master.setMinimumHeight(34)

        grid.addWidget(QLabel("Username"),         0, 0)
        grid.addWidget(self.username,               0, 1)
        grid.addWidget(QLabel("Password"),         1, 0)
        grid.addWidget(self.password,               1, 1)
        grid.addWidget(QLabel("Confirm Password"), 2, 0)
        grid.addWidget(self.confirm_password,       2, 1)
        grid.addWidget(self.show_pass,              3, 1)
        grid.addWidget(QLabel("Setup Code"),       4, 0)
        grid.addWidget(self.master,                 4, 1)

        layout.addLayout(grid)

        btn = QPushButton("Create User")
        btn.setMinimumHeight(38)
        btn.clicked.connect(self.create)
        layout.addWidget(btn)

        self.setLayout(layout)

    def toggle_password(self, state):
        mode = QLineEdit.Normal if state else QLineEdit.Password
        self.password.setEchoMode(mode)
        self.confirm_password.setEchoMode(mode)

    def create(self):
        u = self.username.text().strip()
        p = self.password.text().strip()
        c = self.confirm_password.text().strip()
        m = self.master.text().strip()

        if not u or not p or not c or not m:
            QMessageBox.warning(self, "Error", "Please fill all fields.")
            return

        if p != c:
            QMessageBox.warning(self, "Error", "Passwords do not match ❌")
            return

        if not verify_master_code(m):
            QMessageBox.warning(self, "Error", "Invalid Setup Code ❌")
            return

        result = create_user(self.db_name, u, p)

        if result["success"]:
            self.qr = QRDisplay(result["secret"], result["qr_path"], result["recovery_codes"])
            self.login_window = LoginForm(self.db_name)
            self.login_window  # keep reference alive
            db = self.db_name

            def open_login():
                from PyQt5.QtWidgets import QApplication
                win = LoginForm(db)
                win.show()
                QApplication.instance()._login_ref = win  # prevent GC

            self.qr.destroyed.connect(open_login)
            self.qr.show()
            self.close()
        else:
            QMessageBox.warning(self, "Error", result["message"])

# ──────────────────────────────────────────
#  LOGIN
# ──────────────────────────────────────────
class LoginForm(QWidget):

    def __init__(self, db_name):
        super().__init__()
        self.db_name = db_name

        self.setWindowTitle("Evo Aura — Login")
        self.setFixedSize(420, 290)

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 25, 40, 25)
        layout.setSpacing(14)

        title = QLabel("🔑  Login to Evo Aura")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a7fe8;")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setColumnMinimumWidth(0, 90)
        grid.setColumnMinimumWidth(1, 220)

        self.username = QComboBox()
        self.username.setEditable(True)
        self.username.setInsertPolicy(QComboBox.NoInsert)
        self.username.setPlaceholderText("Select username")
        self.username.setMinimumHeight(34)
        self.load_usernames()

        self.password = QLineEdit()
        self.password.setPlaceholderText("Enter password")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setMinimumHeight(34)
        self.password.returnPressed.connect(self.login)

        grid.addWidget(QLabel("Username"), 0, 0)
        grid.addWidget(self.username,       0, 1)
        grid.addWidget(QLabel("Password"), 1, 0)
        grid.addWidget(self.password,       1, 1)

        layout.addLayout(grid)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_login = QPushButton("Login")
        btn_login.setMinimumHeight(38)
        btn_login.clicked.connect(self.login)

        btn_signup = QPushButton("New User")
        btn_signup.setMinimumHeight(38)
        btn_signup.clicked.connect(self.open_signup)

        btn_row.addWidget(btn_login)
        btn_row.addWidget(btn_signup)
        layout.addLayout(btn_row)

        self.setLayout(layout)

    def load_usernames(self):
        self.username.clear()
        for name in get_all_usernames(self.db_name):
            self.username.addItem(name)
        self.username.setCurrentIndex(-1)

    def login(self):
        u = self.username.currentText().strip()
        p = self.password.text().strip()

        if not u or not p:
            QMessageBox.warning(self, "Error", "Please enter username and password.")
            return

        result = login_user(self.db_name, u, p)

        if not result["success"]:
            QMessageBox.warning(self, "Login Failed", result["message"])
            return

        otp, ok = QInputDialog.getText(
            self, "2FA Verification", "Enter OTP or Recovery Code:"
        )

        if not ok:
            return

        if verify_otp(result["secret"], otp):
            QMessageBox.information(self, "Success", "Login Successful ✅")
            self.dashboard = Dashboard(self.db_name, u)
            self.dashboard.show()
            self.close()
            return

        if otp in result["recovery_codes"]:
            QMessageBox.information(self, "Success", "Login via Recovery Code ✅")
            self.dashboard = Dashboard(self.db_name, u)
            self.dashboard.show()
            self.close()
            return

        QMessageBox.warning(self, "Error", "Invalid OTP / Recovery Code ❌")

    def open_signup(self):
        self.signup = SignupForm(self.db_name)
        self.signup.show()
        self.signup.destroyed.connect(self.load_usernames)

# ──────────────────────────────────────────
#  COMPANY SETTINGS
# ──────────────────────────────────────────

class CompanySettings(QWidget):

    def __init__(self, db_name):
        super().__init__()
        self.db_name = db_name
        self.logo_path = ""

        self.setWindowTitle("Company Settings")
        self.setFixedSize(450, 580)

        layout = QVBoxLayout()
        layout.setContentsMargins(35, 25, 35, 25)
        layout.setSpacing(14)

        # --- TITLE ---
        title = QLabel("🏢  Company Settings")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #1a7fe8;"
        )
        layout.addWidget(title)

        # --- LOGO SECTION ---
        self.logo_label = QLabel()
        self.logo_label.setFixedSize(90, 90)
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setStyleSheet(
            "border: 2px dashed #4da3ff; border-radius: 8px; color: #aaa;"
        )
        self.logo_label.setText("No Logo")

        upload_btn = QPushButton("Upload Logo")
        upload_btn.setFixedHeight(30)
        upload_btn.clicked.connect(self.upload_logo)

        remove_btn = QPushButton("Remove Logo")
        remove_btn.setFixedHeight(30)
        remove_btn.setStyleSheet(
            "background-color:#ff4d4d; color:white;"
        )
        remove_btn.clicked.connect(self.remove_logo)

        logo_row = QHBoxLayout()
        logo_row.addStretch()
        logo_row.addWidget(self.logo_label)
        logo_row.addSpacing(12)

        btn_col = QVBoxLayout()
        btn_col.addWidget(upload_btn)
        btn_col.addWidget(remove_btn)

        logo_row.addLayout(btn_col)
        logo_row.addStretch()

        layout.addLayout(logo_row)

        # --- FORM FIELDS ---
        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setColumnMinimumWidth(0, 120)
        grid.setColumnMinimumWidth(1, 230)

        self.company_name = QLineEdit()
        self.company_name.setPlaceholderText("Company name")
        self.company_name.setMinimumHeight(34)

        self.phone = QLineEdit()
        self.phone.setPlaceholderText("Phone number")
        self.phone.setMinimumHeight(34)

        self.address = QLineEdit()
        self.address.setPlaceholderText("Address")
        self.address.setMinimumHeight(34)

        self.gst = QLineEdit()
        self.gst.setPlaceholderText("GST number")
        self.gst.setMinimumHeight(34)

        self.footer = QTextEdit()
        self.footer.setPlaceholderText("Footer message / description")
        self.footer.setMinimumHeight(90)
        self.footer.setMaximumHeight(110)

        grid.addWidget(QLabel("Company Name"), 0, 0)
        grid.addWidget(self.company_name, 0, 1)

        grid.addWidget(QLabel("Phone"), 1, 0)
        grid.addWidget(self.phone, 1, 1)

        grid.addWidget(QLabel("Address"), 2, 0)
        grid.addWidget(self.address, 2, 1)

        grid.addWidget(QLabel("GST No"), 3, 0)
        grid.addWidget(self.gst, 3, 1)

        grid.addWidget(QLabel("Footer"), 4, 0)
        grid.addWidget(self.footer, 4, 1)

        layout.addLayout(grid)

        # --- SAVE BUTTON ---
        save_btn = QPushButton("Save Settings")
        save_btn.setMinimumHeight(38)
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

        self.setLayout(layout)

        self.load_settings()

    # ---------------- UPLOAD LOGO ----------------
    def upload_logo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Logo", "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            self.logo_path = path

            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self.logo_label.setPixmap(
                    pixmap.scaled(
                        90, 90,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                )
                self.logo_label.setText("")

    # ---------------- REMOVE LOGO ----------------
    def remove_logo(self):
        reply = QMessageBox.question(
            self,
            "Remove Logo",
            "Are you sure you want to remove the logo?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        # clear UI
        self.logo_label.clear()
        self.logo_label.setText("No Logo")
        self.logo_path = ""

        # update DB
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("UPDATE company SET logo=''")
        conn.commit()
        conn.close()

        QMessageBox.information(
            self, "Done", "Logo removed successfully"
        )

    # ---------------- SAVE ----------------
    def save_settings(self):
        try:
            save_company_info(
                self.db_name,
                self.logo_path,
                self.company_name.text().strip(),
                self.phone.text().strip(),
                self.address.text().strip(),
                self.gst.text().strip(),
                self.footer.toPlainText().strip()
            )

            # ✅ success message
            QMessageBox.information(self, "Success", "Company settings saved successfully!")

            # ✅ close the window
            self.close()   # use self.accept() if QDialog

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            QMessageBox.information(
                self, "Saved", "✅ Settings saved successfully!"
            )

    # ---------------- LOAD ----------------
    def load_settings(self):
        data = load_company_info(self.db_name)

        if not data:
            default_name = self.db_name.replace(
                ".db", ""
            ).replace("_", " ").title()

            self.company_name.setText(default_name)
            return

        self.company_name.setText(data.get("company_name", ""))
        self.phone.setText(data.get("phone", ""))
        self.address.setText(data.get("address", ""))
        self.gst.setText(data.get("gst", ""))
        self.footer.setPlainText(data.get("footer", ""))

        logo = data.get("logo")

        # FIXED: load from path correctly
        if logo:
            pixmap = QPixmap(logo)
            if not pixmap.isNull():
                self.logo_label.setPixmap(
                    pixmap.scaled(
                        90, 90,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                )
                self.logo_label.setText("")
            else:
                self.logo_label.setText("No Logo")
        else:
            self.logo_label.setText("No Logo")
# ──────────────────────────────────────────
#  DASHBOARD
# ──────────────────────────────────────────

class Dashboard(QWidget):

    def __init__(self, db_name, username="User"):
        super().__init__()
        self.db_name = db_name

        company = load_company_info(self.db_name)
        company_name = company.get("company_name", "Your Company")
        logo_pixmap = company.get("logo")

        self.setWindowTitle("Evo Aura Billing")
        self.showMaximized()
        self.setStyleSheet("background-color: #f4f7fb;")

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(15)

        # ── TOP BAR ──
        top_frame = QFrame()
        top_frame.setFixedHeight(70)
        top_frame.setStyleSheet("background: white; border-radius: 10px;")

        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(20, 5, 20, 5)

        logo = QLabel()
        logo.setFixedSize(40, 40)
        pixmap = QPixmap("icon/auralogo.png")
        if not pixmap.isNull():
            logo.setPixmap(
                pixmap.scaled(logo.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )

        app_name = QLabel("Evo Aura")
        app_name.setFont(QFont("Segoe UI", 14, QFont.Bold))
        app_name.setStyleSheet("color: #1a7fe8;")

        dash_title = QLabel("Dashboard")
        dash_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        dash_title.setAlignment(Qt.AlignCenter)

        # 👨🏻‍💼 USER BUTTON
        user_btn = QPushButton(f"👨🏻‍💼  {username}")
        user_btn.setCursor(Qt.PointingHandCursor)
        user_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 16px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background: #eef5ff;
                border-radius: 6px;
            }
        """)
        user_btn.clicked.connect(lambda: self.open_user_security(username))

        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.setCursor(Qt.PointingHandCursor)
        settings_btn.setFixedHeight(32)
        settings_btn.setFixedWidth(95)
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color : #eef5ff;
                border-radius    : 6px;
                padding          : 4px 10px;
                font-weight      : bold;
                border           : 1px solid #4da3ff;
            }
            QPushButton:hover { background-color: #ddeeff; }
        """)
        settings_btn.clicked.connect(self.open_settings)

        logout_btn = QPushButton("Logout")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setFixedHeight(32)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color : #ff5c5c;
                color            : white;
                border-radius    : 6px;
                padding          : 4px 14px;
                font-weight      : bold;
                border           : none;
            }
            QPushButton:hover { background-color: #ff3b3b; }
        """)
        logout_btn.clicked.connect(self.close)

        top_layout.addWidget(logo)
        top_layout.addWidget(app_name)
        top_layout.addStretch()
        top_layout.addWidget(dash_title)
        top_layout.addStretch()
        top_layout.addWidget(user_btn)
        top_layout.addWidget(settings_btn)
        top_layout.addWidget(logout_btn)

        main_layout.addWidget(top_frame)
        #-------------------------------------------------------
        #                     ── MAIN CARD ──
        #------------------------------------------------------
        card = QFrame()
        card.setStyleSheet("""
            background: white;
            border-radius: 14px;
        """)

        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(50, 30, 50, 30)
        card_layout.setSpacing(20)

            
        # ── WELCOME SECTION    IMAGE ──
        if logo_pixmap and not logo_pixmap.isNull():
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(10)

            img_label = QLabel()
            img_label.setFixedSize(200, 200)

            img_label.setPixmap(
                logo_pixmap.scaled(
                    img_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            )

            welcome = QLabel(f"Welcome, {company_name}")
            welcome.setFont(QFont("Segoe UI", 26, QFont.Bold))

            # ✅ Proper LEFT → RIGHT layout
            layout.addStretch()
            layout.addWidget(img_label)
            layout.addWidget(welcome)
            layout.addStretch()

            container.setStyleSheet("background-color: #eef5ff;")
            card_layout.addWidget(container)

        else:
            welcome = QLabel(f"Welcome, {company_name}")
            welcome.setAlignment(Qt.AlignCenter)
            welcome.setFont(QFont("Segoe UI", 26, QFont.Bold))
            welcome.setStyleSheet("background-color: #eef5ff;")

            card_layout.addWidget(welcome)

        # ── GRID BUTTONS ──
        grid = QGridLayout()
        grid.setSpacing(20)

        def make_card_btn(text, action):
            btn = QPushButton(text)
            btn.setMinimumHeight(110)
            btn.setStyleSheet("""
                QPushButton {
                    background-color : #ffffff;
                    border           : 1px solid #d6e4f0;
                    border-radius    : 12px;
                    font-size        : 17px;
                    font-weight      : 600;
                    padding          : 15px;
                }
                QPushButton:hover {
                    background-color : #f0f7ff;
                    border           : 1px solid #4da3ff;
                }
            """)
            btn.clicked.connect(lambda: self.coming_soon(action))
            return btn

        grid.addWidget(make_card_btn("✚   Add Product", "Add Product"), 0, 0)
        grid.addWidget(make_card_btn("🏷️   Sale", "Sale"), 0, 1)
        grid.addWidget(make_card_btn("🔁   Return", "Return"), 1, 0)
        grid.addWidget(make_card_btn("🧾   Bill Views", "Bill View"), 1, 1)
        grid.addWidget(make_card_btn("📊   Report Insights", "Report"), 2, 0, 1, 2)

        card_layout.addLayout(grid)
        card.setLayout(card_layout)
        main_layout.addWidget(card)

        self.setLayout(main_layout)

    # 🔐 USER SECURITY
    def open_user_security(self, username):
        otp, ok = QInputDialog.getText(
            self,
            "Verify Identity",
            "Enter your 6-digit OTP:",
            QLineEdit.Normal
        )

        if not ok or not otp:
            return

        if len(otp) != 6 or not otp.isdigit():
            QMessageBox.warning(self, "Error", "Enter valid 6-digit code")
            return

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT otp_secret, recovery_codes
            FROM users
            WHERE username=?
        """, (username,))

        data = cursor.fetchone()
        conn.close()

        if not data:
            QMessageBox.warning(self, "Error", "User not found")
            return

        secret, recovery_codes = data
        recovery_codes = recovery_codes.split(",") if recovery_codes else []

        if not verify_otp(secret, otp):
            QMessageBox.warning(self, "Error", "Invalid OTP ❌")
            return

        qr_path = generate_qr(secret, username)

        self.qr_view = QRDisplay(secret, qr_path, recovery_codes)
        self.qr_view.show()

    # ⚙️ SETTINGS
    def open_settings(self):
        self.settings_win = CompanySettings(self.db_name)
        self.settings_win.show()

    # 🚀 COMING SOON
    def coming_soon(self, page):
        QMessageBox.information(self, page, f"{page} — Coming Soon 🚀")

# ──────────────────────────────────────────
#  MAIN ENTRY
# ──────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)

    db_files = glob.glob("*.db")

    if db_files:
        db_name = db_files[0]
        init_db(db_name)
        if has_users(db_name):
            window = LoginForm(db_name)
        else:
            window = SignupForm(db_name)
    else:
        window = AskDBName()

    window.show()
    sys.exit(app.exec_())