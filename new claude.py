import sys
import os
import glob
import sqlite3
import random
import string
import pyotp
import qrcode

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

from product_page import ProductPage

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel,
    QLineEdit, QGridLayout, QMessageBox, QInputDialog,
    QVBoxLayout, QHBoxLayout, QFrame, QComboBox,
    QCheckBox, QTextEdit, QFileDialog,QStackedWidget
)
from PyQt5.QtGui import QPixmap, QFont, QIcon
from PyQt5.QtCore import Qt


# ─────────────────────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────────────────────

MASTER_SECRET = "KRSXG5DSNFXGOIDB"   # TOTP secret used for all master-code checks


# ─────────────────────────────────────────────────────────────
#  GENERIC HELPERS
# ─────────────────────────────────────────────────────────────

def verify_master_code(code: str) -> bool:
    """Return True if *code* is a valid TOTP value for MASTER_SECRET."""
    return pyotp.TOTP(MASTER_SECRET).verify(code)


def verify_otp(secret: str, otp: str) -> bool:
    """Return True if *otp* is a valid TOTP value for *secret*."""
    return pyotp.TOTP(secret).verify(otp)


def generate_recovery_codes(n: int = 5) -> list:
    """Generate *n* random 8-character alphanumeric recovery codes."""
    chars = string.ascii_uppercase + string.digits
    return [''.join(random.choices(chars, k=8)) for _ in range(n)]


def generate_qr(secret: str, username: str) -> str:
    """
    Build a TOTP provisioning URI and save the QR-code PNG.
    Returns the saved file path ('<username>_qr.png').
    """
    uri = pyotp.TOTP(secret).provisioning_uri(name=username, issuer_name="EvoAura")
    path = f"{username}_qr.png"
    qrcode.make(uri).save(path)
    return path


def pixmap_from_blob(blob) -> QPixmap:
    """
    Convert a logo value from the DB into a QPixmap.
    Handles both raw BLOB (bytes) and legacy file-path strings.
    Returns an empty QPixmap on failure.
    """
    px = QPixmap()
    if isinstance(blob, (bytes, bytearray)):
        px.loadFromData(blob)
    elif isinstance(blob, str) and os.path.exists(blob):
        px.load(blob)
    return px


def px_scaled(pixmap: QPixmap, w: int, h: int) -> QPixmap:
    """Scale *pixmap* to (w, h) keeping aspect ratio with smooth interpolation."""
    return pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)


def alert(parent, title: str, msg: str, kind: str = "info"):
    """
    Show a themed QMessageBox.
      kind='info'  -> QMessageBox.information
      kind='warn'  -> QMessageBox.warning
      kind='error' -> QMessageBox.critical
    """
    dispatch = {
        "info" : QMessageBox.information,
        "warn" : QMessageBox.warning,
        "error": QMessageBox.critical,
    }
    dispatch.get(kind, QMessageBox.information)(parent, title, msg)


# ─────────────────────────────────────────────────────────────
#  DATABASE — USERS
# ─────────────────────────────────────────────────────────────

def init_db(db_name: str):
    """
    Create the *users* and *company_info* tables if they don't exist.
    Safe to call repeatedly on an already-initialised database.
    """
    with sqlite3.connect(db_name) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                username       TEXT UNIQUE,
                password       TEXT,
                role           TEXT,
                otp_secret     TEXT,
                recovery_codes TEXT
            );

            CREATE TABLE IF NOT EXISTS company_info (
                id           INTEGER PRIMARY KEY,
                logo         BLOB,
                company_name TEXT,
                phone        TEXT,
                address      TEXT,
                gst          TEXT,
                footer       TEXT
            );
        """)


def has_users(db_name: str) -> bool:
    """Return True if at least one user row exists in *db_name*."""
    with sqlite3.connect(db_name) as conn:
        return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0


def get_all_usernames(db_name: str) -> list:
    """Return a sorted list of all usernames in *db_name*."""
    with sqlite3.connect(db_name) as conn:
        rows = conn.execute("SELECT username FROM users ORDER BY username").fetchall()
    return [r[0] for r in rows]


def create_user(db_name: str, username: str, password: str, role: str = "user") -> dict:
    """
    Insert a new user, generate their TOTP secret and recovery codes.
    Returns {'success': True, 'secret', 'recovery_codes', 'qr_path'} on success,
    or {'success': False, 'message'} on failure (e.g. duplicate username).
    """
    secret  = pyotp.random_base32()
    codes   = generate_recovery_codes()
    qr_path = generate_qr(secret, username)

    try:
        with sqlite3.connect(db_name) as conn:
            conn.execute(
                "INSERT INTO users VALUES (NULL, ?, ?, ?, ?, ?)",
                (username, password, role, secret, ",".join(codes))
            )
        return {"success": True, "secret": secret,
                "recovery_codes": codes, "qr_path": qr_path}
    except sqlite3.IntegrityError:
        return {"success": False, "message": "Username already exists"}


def login_user(db_name: str, username: str, password: str) -> dict:
    """
    Validate username + password.
    Returns {'success': True, 'secret', 'role', 'recovery_codes'} on success,
    or {'success': False, 'message'} on failure.
    """
    with sqlite3.connect(db_name) as conn:
        row = conn.execute(
            "SELECT password, otp_secret, role, recovery_codes FROM users WHERE username=?",
            (username,)
        ).fetchone()

    if not row:
        return {"success": False, "message": "User not found"}

    db_pass, secret, role, codes = row
    if password != db_pass:
        return {"success": False, "message": "Wrong password"}

    return {
        "success"       : True,
        "secret"        : secret,
        "role"          : role,
        "recovery_codes": codes.split(",") if codes else []
    }


def get_user_otp_data(db_name: str, username: str):
    """
    Return (otp_secret, recovery_codes_list) for *username*.
    Returns (None, []) if the user is not found.
    Used by the dashboard user-security viewer.
    """
    with sqlite3.connect(db_name) as conn:
        row = conn.execute(
            "SELECT otp_secret, recovery_codes FROM users WHERE username=?",
            (username,)
        ).fetchone()

    if not row:
        return None, []
    secret, codes = row
    return secret, (codes.split(",") if codes else [])


# ─────────────────────────────────────────────────────────────
#  DATABASE — COMPANY INFO
# ─────────────────────────────────────────────────────────────

def save_company_info(db_name: str, logo_path: str, company_name: str,
                      phone: str, address: str, gst: str, footer: str):
    """
    Upsert the single company-info row (id=1).
    *logo_path* is read from disk and stored as raw BLOB bytes.
    Pass an empty string for *logo_path* to leave the logo column NULL.
    """
    logo_data = None
    if logo_path and os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_data = f.read()

    with sqlite3.connect(db_name) as conn:
        exists = conn.execute("SELECT id FROM company_info WHERE id=1").fetchone()
        if exists:
            conn.execute(
                "UPDATE company_info SET logo=?,company_name=?,phone=?,address=?,gst=?,footer=? WHERE id=1",
                (logo_data, company_name, phone, address, gst, footer)
            )
        else:
            conn.execute(
                "INSERT INTO company_info (id,logo,company_name,phone,address,gst,footer) VALUES (1,?,?,?,?,?,?)",
                (logo_data, company_name, phone, address, gst, footer)
            )


def clear_company_logo(db_name: str):
    """Set the stored logo to NULL without touching any other company fields."""
    with sqlite3.connect(db_name) as conn:
        conn.execute("UPDATE company_info SET logo=NULL WHERE id=1")


def load_company_info(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT logo, company_name, phone, address, gst, footer FROM company_info WHERE id=1"
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "logo"         : row[0] or "",
            "company_name" : row[1] or "",
            "phone"        : row[2] or "",
            "address"      : row[3] or "",
            "gst"          : row[4] or "",
            "footer"       : row[5] or ""
        }
    return {}


# ─────────────────────────────────────────────────────────────
#  QR DISPLAY
# ─────────────────────────────────────────────────────────────

class QRDisplay(QWidget):
    """
    Shows the TOTP QR-code image, the raw secret key, and recovery codes.
    The user scans the QR in Google Authenticator / Authy.
    Provides a 'Copy Codes' button for convenience.
    """

    def __init__(self, secret: str, qr_path: str, recovery_codes: list):
        super().__init__()
        self.recovery_codes = recovery_codes

        self.setWindowTitle("Setup 2FA")
        self.setFixedSize(420, 560)

        layout = QVBoxLayout()
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(12)

        # Title
        title = QLabel("📱  Scan QR in Authenticator App")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #1a7fe8;")
        layout.addWidget(title)

        # QR code image
        qr_label = QLabel()
        qr_label.setPixmap(px_scaled(QPixmap(qr_path), 200, 200))
        qr_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(qr_label)

        # Secret key display
        lbl_s = QLabel(f"🔑  Secret Key:\n{secret}")
        lbl_s.setWordWrap(True)
        lbl_s.setStyleSheet(
            "font-size: 12px; background:#f0f7ff; padding:8px; border-radius:5px;"
        )
        layout.addWidget(lbl_s)

        # Recovery codes display
        self.lbl_r = QLabel(
            "🛡  Recovery Codes (save these!):\n" + "\n".join(recovery_codes)
        )
        self.lbl_r.setWordWrap(True)
        self.lbl_r.setStyleSheet(
            "font-size: 12px; background:#fff7e6; padding:8px; border-radius:5px;"
        )
        layout.addWidget(self.lbl_r)

        # Buttons row
        btn_row = QHBoxLayout()

        copy_btn = QPushButton("📋 Copy Codes")
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.setMinimumHeight(34)
        copy_btn.clicked.connect(self._copy_codes)

        done_btn = QPushButton("✅ Done")
        done_btn.setMinimumHeight(34)
        done_btn.clicked.connect(self.close)

        btn_row.addWidget(copy_btn)
        btn_row.addWidget(done_btn)
        layout.addLayout(btn_row)

        self.setLayout(layout)

    def _copy_codes(self):
        """Copy all recovery codes to the system clipboard."""
        QApplication.clipboard().setText("\n".join(self.recovery_codes))
        alert(self, "Copied", "Recovery codes copied to clipboard ✅")


# ─────────────────────────────────────────────────────────────
#  STEP 1 — ASK DB / COMPANY NAME  (first-run wizard)
# ─────────────────────────────────────────────────────────────

class AskDBName(QWidget):
    """
    First-run wizard step 1: asks for a company name that becomes the DB filename.
    Prevents overwriting an existing database.
    """

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
        self.db_input.returnPressed.connect(self._go_next)
        layout.addWidget(self.db_input)

        btn = QPushButton("Next  →")
        btn.setMinimumHeight(38)
        btn.clicked.connect(self._go_next)
        layout.addWidget(btn)

        self.setLayout(layout)

    def _go_next(self):
        """Sanitise the entered name and open master-code verification."""
        name = self.db_input.text().strip().replace(" ", "_")
        if not name:
            alert(self, "Error", "Please enter a Company name.", "warn")
            return

        if not name.endswith(".db"):
            name += ".db"

        if os.path.exists(name):
            alert(self, "Already Exists",
                  f"'{name}' already exists.\nPlease choose a different name.", "warn")
            return

        self.auth = StartupAuth(name)
        self.auth.show()
        self.close()


# ─────────────────────────────────────────────────────────────
#  STEP 2 — MASTER CODE VERIFICATION  (first-run wizard)
# ─────────────────────────────────────────────────────────────

class StartupAuth(QWidget):
    """
    First-run wizard step 2: verifies the TOTP master code before
    creating a new database.  On success initialises the DB, saves
    a default company name, then opens CompanySettings -> SignupForm.
    """

    def __init__(self, db_name: str):
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
        self.otp_input.returnPressed.connect(self._verify)
        layout.addWidget(self.otp_input)

        btn = QPushButton("Verify & Create Database")
        btn.setMinimumHeight(38)
        btn.clicked.connect(self._verify)
        layout.addWidget(btn)

        self.setLayout(layout)

    def _verify(self):
        """Check master code -> create DB -> open company settings."""
        code = self.otp_input.text().strip()
        if not verify_master_code(code):
            alert(self, "Error", "Invalid Master Code ❌\nPlease try again.", "warn")
            self.otp_input.clear()
            return

        init_db(self.db_name)

        # Derive a human-readable default company name from the filename
        default_name = self.db_name.replace(".db", "").replace("_", " ").title()
        save_company_info(self.db_name, "", default_name, "", "", "", "")

        alert(self, "Database Created",
              f"✅  '{self.db_name}' created successfully!\nNow create the first user.")

        # Open company settings; when closed, open signup automatically
        self.company_form = CompanySettings(self.db_name)
        self.company_form.destroyed.connect(self._open_signup)
        self.company_form.show()
        self.close()

    def _open_signup(self):
        """Called automatically after CompanySettings window is closed."""
        self.signup = SignupForm(self.db_name)
        self.signup.show()


# ─────────────────────────────────────────────────────────────
#  SIGNUP
# ─────────────────────────────────────────────────────────────

class SignupForm(QWidget):
    """
    Creates a new user account (username + password + TOTP 2FA).
    Requires the master TOTP code to authorise account creation.
    On success shows the QR / recovery-code screen, then opens LoginForm.
    """

    def __init__(self, db_name: str):
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
        self.show_pass.stateChanged.connect(self._toggle_password)

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
        btn.clicked.connect(self._create)
        layout.addWidget(btn)

        self.setLayout(layout)

    def _toggle_password(self, state: int):
        """Toggle plain / hidden text for both password fields simultaneously."""
        mode = QLineEdit.Normal if state else QLineEdit.Password
        self.password.setEchoMode(mode)
        self.confirm_password.setEchoMode(mode)

    def _create(self):
        """Validate all inputs, create the user, show QR on success."""
        u = self.username.text().strip()
        p = self.password.text().strip()
        c = self.confirm_password.text().strip()
        m = self.master.text().strip()

        if not all([u, p, c, m]):
            alert(self, "Error", "Please fill all fields.", "warn")
            return
        if p != c:
            alert(self, "Error", "Passwords do not match ❌", "warn")
            return
        if not verify_master_code(m):
            alert(self, "Error", "Invalid Setup Code ❌", "warn")
            return

        result = create_user(self.db_name, u, p)
        if not result["success"]:
            alert(self, "Error", result["message"], "warn")
            return

        db = self.db_name

        def _open_login():
            """Open LoginForm after the QR window is closed."""
            win = LoginForm(db)
            win.show()
            # Keep reference on the app object to prevent garbage collection
            QApplication.instance()._login_ref = win

        self.qr = QRDisplay(result["secret"], result["qr_path"], result["recovery_codes"])
        self.qr.destroyed.connect(_open_login)
        self.qr.show()
        self.close()


# ─────────────────────────────────────────────────────────────
#  LOGIN
# ─────────────────────────────────────────────────────────────

class LoginForm(QWidget):
    """
    Standard login screen: username dropdown + password -> OTP / recovery-code check.
    Offers a 'New User' button that opens SignupForm without closing the login window.
    """

    def __init__(self, db_name: str):
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
        self._load_usernames()

        self.password = QLineEdit()
        self.password.setPlaceholderText("Enter password")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setMinimumHeight(34)
        self.password.returnPressed.connect(self._login)

        grid.addWidget(QLabel("Username"), 0, 0)
        grid.addWidget(self.username,       0, 1)
        grid.addWidget(QLabel("Password"), 1, 0)
        grid.addWidget(self.password,       1, 1)
        layout.addLayout(grid)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_login = QPushButton("Login")
        btn_login.setMinimumHeight(38)
        btn_login.clicked.connect(self._login)

        btn_signup = QPushButton("New User")
        btn_signup.setMinimumHeight(38)
        btn_signup.clicked.connect(self._open_signup)

        btn_row.addWidget(btn_login)
        btn_row.addWidget(btn_signup)
        layout.addLayout(btn_row)

        self.setLayout(layout)

    def _load_usernames(self):
        """Refresh the username dropdown from the database."""
        self.username.clear()
        for name in get_all_usernames(self.db_name):
            self.username.addItem(name)
        self.username.setCurrentIndex(-1)

    def _login(self):
        """Verify password then prompt for OTP / recovery code."""
        u = self.username.currentText().strip()
        p = self.password.text().strip()

        if not u or not p:
            alert(self, "Error", "Please enter username and password.", "warn")
            return

        result = login_user(self.db_name, u, p)
        if not result["success"]:
            alert(self, "Login Failed", result["message"], "warn")
            return

        otp, ok = QInputDialog.getText(
            self, "2FA Verification", "Enter OTP or Recovery Code:"
        )
        if not ok:
            return

        if verify_otp(result["secret"], otp) or otp in result["recovery_codes"]:
            alert(self, "Success", "Login Successful ✅")
            self.dashboard = Dashboard(self.db_name, u)
            self.dashboard.show()
            self.close()
        else:
            alert(self, "Error", "Invalid OTP / Recovery Code ❌", "warn")

    def _open_signup(self):
        """Open signup form; reload usernames when it is closed."""
        self.signup = SignupForm(self.db_name)
        self.signup.destroyed.connect(self._load_usernames)
        self.signup.show()


# ─────────────────────────────────────────────────────────────
#  COMPANY SETTINGS
# ─────────────────────────────────────────────────────────────

class CompanySettings(QWidget):
    """
    Editor for company branding: logo (upload/remove), company name, phone,
    address, GST number, and invoice footer text.
    Settings are persisted to the *company_info* table.
    """

    def __init__(self, db_name: str):
        super().__init__()
        self.db_name   = db_name
        self.logo_path = ""     # tracks path of a newly chosen logo file

        self.setWindowTitle("Company Settings")
        self.setFixedSize(450, 580)

        layout = QVBoxLayout()
        layout.setContentsMargins(35, 25, 35, 25)
        layout.setSpacing(14)

        # Title
        title = QLabel("🏢  Company Settings")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a7fe8;")
        layout.addWidget(title)

        # ── LOGO SECTION ──────────────────────────────────────
        self.logo_label = QLabel()
        self.logo_label.setFixedSize(90, 90)
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setStyleSheet(
            "border: 2px dashed #4da3ff; border-radius: 8px; color: #aaa;"
        )
        self.logo_label.setText("No Logo")

        upload_btn = QPushButton("Upload Logo")
        upload_btn.setFixedHeight(30)
        upload_btn.clicked.connect(self._upload_logo)

        remove_btn = QPushButton("Remove Logo")
        remove_btn.setFixedHeight(30)
        remove_btn.setStyleSheet("background-color:#ff4d4d; color:white;")
        remove_btn.clicked.connect(self._remove_logo)

        btn_col = QVBoxLayout()
        btn_col.addWidget(upload_btn)
        btn_col.addWidget(remove_btn)

        logo_row = QHBoxLayout()
        logo_row.addStretch()
        logo_row.addWidget(self.logo_label)
        logo_row.addSpacing(12)
        logo_row.addLayout(btn_col)
        logo_row.addStretch()
        layout.addLayout(logo_row)

        # ── FORM FIELDS ───────────────────────────────────────
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

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setColumnMinimumWidth(0, 120)
        grid.setColumnMinimumWidth(1, 230)

        grid.addWidget(QLabel("Company Name"), 0, 0)
        grid.addWidget(self.company_name,       0, 1)
        grid.addWidget(QLabel("Phone"),        1, 0)
        grid.addWidget(self.phone,              1, 1)
        grid.addWidget(QLabel("Address"),      2, 0)
        grid.addWidget(self.address,            2, 1)
        grid.addWidget(QLabel("GST No"),       3, 0)
        grid.addWidget(self.gst,               3, 1)
        grid.addWidget(QLabel("Footer"),       4, 0)
        grid.addWidget(self.footer,            4, 1)

        layout.addLayout(grid)

        save_btn = QPushButton("Save Settings")
        save_btn.setMinimumHeight(38)
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)

        self.setLayout(layout)
        self._load()

    # ── LOGO ACTIONS ─────────────────────────────────────────

    def _upload_logo(self):
        """Open a file dialog to select a logo image and preview it."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Logo", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            self.logo_path = path
            px = QPixmap(path)
            if not px.isNull():
                self.logo_label.setPixmap(px_scaled(px, 90, 90))
                self.logo_label.setText("")

    def _remove_logo(self):
        """Clear the logo from the preview and the database after confirmation."""
        reply = QMessageBox.question(
            self, "Remove Logo",
            "Are you sure you want to remove the logo?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        self.logo_label.clear()
        self.logo_label.setText("No Logo")
        self.logo_path = ""
        clear_company_logo(self.db_name)   # BUG FIX: was querying wrong table 'company'
        alert(self, "Done", "Logo removed successfully")

    # ── SAVE / LOAD ──────────────────────────────────────────

    def _save(self):
        """Persist all company fields to the database, then close the window."""
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
            alert(self, "Success", "Company settings saved successfully!")
            self.close()
            # BUG FIX: removed the stray second QMessageBox that always fired
        except Exception as e:
            alert(self, "Error", str(e), "error")

    def _load(self):
        """Populate all fields from the database (falls back to filename-derived default)."""
        data = load_company_info(self.db_name)
        if not data:
            default = self.db_name.replace(".db", "").replace("_", " ").title()
            self.company_name.setText(default)
            return

        self.company_name.setText(data.get("company_name", ""))
        self.phone.setText(data.get("phone", ""))
        self.address.setText(data.get("address", ""))
        self.gst.setText(data.get("gst", ""))
        self.footer.setPlainText(data.get("footer", ""))

        logo = data.get("logo", "")
        if isinstance(logo, (bytes, bytearray)):
            logo = logo.decode("utf-8", errors="ignore").strip()
        if logo and os.path.exists(logo):
            px = QPixmap(logo)
            if not px.isNull():
                self.logo_path = logo
                self.logo_label.setPixmap(px.scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.logo_label.setText("")
            else:
                self.logo_label.setText("No Logo")
        else:
            self.logo_label.setText("No Logo")


# ─────────────────────────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────────────────────────

class Dashboard(QWidget):

    def __init__(self, db_name: str, username: str = "User"):
        super().__init__()
        self.db_name  = db_name
        self.username = username

        company      = load_company_info(db_name)
        company_name = company.get("company_name", "Your Company")
        logo_path = company.get("logo") or ""

        self.setWindowTitle("Evo Aura Billing")
        self.showMaximized()
        self.setStyleSheet("background-color: #f4f7fb;")

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(15)

        self.topbar = self._build_topbar()
        main_layout.addWidget(self.topbar)

        # ── STACK: page 0 = dashboard card, page 1+ = modules ──
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_card(company_name, logo_path))
        main_layout.addWidget(self.stack)

        self.setLayout(main_layout)

    # ── TOP BAR ──────────────────────────────────────────────

    def _build_topbar(self) -> QFrame:
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
                pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )

        app_name = QLabel("Evo Aura")
        app_name.setFont(QFont("Segoe UI", 14, QFont.Bold))
        app_name.setStyleSheet("color: #1a7fe8;")

        dash_title = QLabel("Dashboard")
        dash_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        dash_title.setAlignment(Qt.AlignCenter)

        user_btn = QPushButton(f"👤  {self.username}")
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
        user_btn.clicked.connect(lambda: self._open_user_security(self.username))

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
        settings_btn.clicked.connect(self._open_settings)

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

        return top_frame

    # ── MAIN CARD ────────────────────────────────────────────

    def _build_card(self, company_name: str, logo_path: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet("background: white; border-radius: 14px;")

        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(50, 30, 50, 30)
        card_layout.setSpacing(20)

        # Welcome banner
        welcome_frame = QFrame()
        welcome_frame.setFixedHeight(120)
        welcome_frame.setStyleSheet("background-color: #eef5ff; border-radius: 10px;")

        welcome_layout = QHBoxLayout(welcome_frame)
        welcome_layout.setContentsMargins(20, 10, 20, 10)
        welcome_layout.setSpacing(16)

        if logo_path and os.path.exists(logo_path):
            img_label = QLabel()
            img_label.setFixedSize(90, 90)
            img_label.setPixmap(
                QPixmap(logo_path).scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            img_label.setStyleSheet("background: transparent;")
            welcome_layout.addWidget(img_label)

        welcome = QLabel(f"Welcome, {company_name}")
        welcome.setFont(QFont("Segoe UI", 26, QFont.Bold))
        welcome.setStyleSheet("background: transparent; color: #1a7fe8;")
        welcome_layout.addWidget(welcome)
        welcome_layout.addStretch()

        card_layout.addWidget(welcome_frame)

        # Module grid
        grid = QGridLayout()
        grid.setSpacing(20)

        btn_product = self._make_card_btn("✚  Add Product", "Add Product")
        btn_product.clicked.disconnect()
        btn_product.clicked.connect(self.open_products)
        grid.addWidget(btn_product, 0, 0)

        btn_sale = self._make_card_btn("🏷️ Sale", "Sale")
        btn_sale.clicked.disconnect()
        btn_sale.clicked.connect(self.open_billing)
        grid.addWidget(btn_sale, 0, 1)

        grid.addWidget(self._make_card_btn("🔁   Return",         "Return"), 1, 0)
        grid.addWidget(self._make_card_btn("🧾   Bill Views",     "Bill View"), 1, 1)
        grid.addWidget(self._make_card_btn("📊   Report Insights","Report"), 2, 0, 1, 2)

        card_layout.addLayout(grid)
        card.setLayout(card_layout)
        return card

    # ── MODULE NAVIGATION ────────────────────────────────────

    def open_products(self):
        from product_page import ProductPage
        company      = load_company_info(self.db_name)
        company_name = company.get("company_name", "")
        self.product_page = ProductPage(
            self.db_name,
            company_name=company_name,
            on_back=self.close_products
        )
        self.stack.addWidget(self.product_page)
        self.stack.setCurrentWidget(self.product_page)
        self.topbar.setVisible(False)      # ← hide dashboard topbar

    def close_products(self):
        self.topbar.setVisible(True)       # ← show dashboard topbar again
        self.stack.setCurrentIndex(0)
        if self.stack.count() > 1:
            widget = self.stack.widget(1)
            self.stack.removeWidget(widget)
            widget.deleteLater()


    def open_billing(self):
        from billing_page import BillingPage
        company = load_company_info(self.db_name)
        self.billing_page = BillingPage(
            self.db_name,
            company_name=company.get("company_name", ""),
            on_back=self.close_billing
        )
        self.stack.addWidget(self.billing_page)
        self.stack.setCurrentWidget(self.billing_page)
        self.topbar.setVisible(False)

    def close_billing(self):
        self.topbar.setVisible(True)
        self.stack.setCurrentIndex(0)
        if self.stack.count() > 1:
            w = self.stack.widget(1)
            self.stack.removeWidget(w)
            w.deleteLater()

    # ── HELPERS ──────────────────────────────────────────────

    def _make_card_btn(self, text: str, action: str) -> QPushButton:
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
        btn.clicked.connect(lambda: self._coming_soon(action))
        return btn

    def _open_user_security(self, username: str):
        otp, ok = QInputDialog.getText(
            self, "Verify Identity", "Enter your 6-digit OTP:", QLineEdit.Normal
        )
        if not ok or not otp:
            return

        if len(otp) != 6 or not otp.isdigit():
            QMessageBox.warning(self, "Error", "Enter valid 6-digit code")
            return

        conn   = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT otp_secret, recovery_codes FROM users WHERE username=?", (username,)
        )
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

        qr_path      = generate_qr(secret, username)
        self.qr_view = QRDisplay(secret, qr_path, recovery_codes)
        self.qr_view.show()

    def _open_settings(self):
        self.settings_win = CompanySettings(self.db_name)
        self.settings_win.show()

    def _coming_soon(self, page: str):
        QMessageBox.information(self, page, f"{page} — Coming Soon 🚀")


# ─────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)

    db_files = glob.glob("*.db")

    if db_files:
        # Use the first database found in the working directory
        db_name = db_files[0]
        init_db(db_name)
        window = LoginForm(db_name) if has_users(db_name) else SignupForm(db_name)
    else:
        # No database yet — run the first-time setup wizard
        window = AskDBName()

    window.show()
    sys.exit(app.exec_())