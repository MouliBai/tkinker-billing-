import sys
import os
import glob

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QLabel,
    QLineEdit,
    QGridLayout,
    QMessageBox,
    QInputDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QComboBox
)

from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt

import sqlite3
import pyotp
import qrcode
import random
import string

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


def has_users(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0


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
#  USER FUNCTIONS  (all accept db_name)
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
        self.setWindowTitle("Setup 2FA")
        self.setFixedSize(420, 530)

        layout = QVBoxLayout()
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(12)

        title = QLabel("📱  Scan QR in Authenticator App")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #1a7fe8;")
        layout.addWidget(title)

        qr_label = QLabel()
        pixmap   = QPixmap(qr_path).scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        qr_label.setPixmap(pixmap)
        qr_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(qr_label)

        lbl_s = QLabel(f"🔑  Secret Key:\n{secret}")
        lbl_s.setWordWrap(True)
        lbl_s.setStyleSheet(
            "font-size: 12px; background:#f0f7ff; padding:8px; border-radius:5px;"
        )
        layout.addWidget(lbl_s)

        lbl_r = QLabel("🛡  Recovery Codes (save these!):\n" + "\n".join(recovery_codes))
        lbl_r.setWordWrap(True)
        lbl_r.setStyleSheet(
            "font-size: 12px; background:#fff7e6; padding:8px; border-radius:5px;"
        )
        layout.addWidget(lbl_r)

        btn = QPushButton("✅  Done")
        btn.setMinimumHeight(38)
        btn.clicked.connect(self.close)
        layout.addWidget(btn)

        self.setLayout(layout)


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

        title = QLabel("🗄  Create New Database")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a7fe8;")
        layout.addWidget(title)

        sub = QLabel("Enter a name for your database file.")
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
            QMessageBox.warning(self, "Error", "Please enter a database name.")
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

        # ✅ Correct — create DB now
        init_db(self.db_name)

        QMessageBox.information(
            self, "Database Created",
            f"✅  '{self.db_name}' created successfully!\nNow create the first user."
        )

        self.signup = SignupForm(self.db_name)
        self.signup.show()
        self.close()


# ──────────────────────────────────────────
#  SIGNUP
# ──────────────────────────────────────────
class SignupForm(QWidget):

    def __init__(self, db_name):
        super().__init__()
        self.db_name = db_name

        self.setWindowTitle("Create User")
        self.setFixedSize(420, 310)

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 25, 40, 25)
        layout.setSpacing(14)

        title = QLabel("👤  Create New User")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a7fe8;")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setColumnMinimumWidth(0, 90)
        grid.setColumnMinimumWidth(1, 220)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Enter username")
        self.username.setMinimumHeight(34)

        self.password = QLineEdit()
        self.password.setPlaceholderText("Enter password")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setMinimumHeight(34)

        self.master = QLineEdit()
        self.master.setPlaceholderText("6-digit TOTP code")
        self.master.setEchoMode(QLineEdit.Password)
        self.master.setMinimumHeight(34)

        grid.addWidget(QLabel("Username"),   0, 0)
        grid.addWidget(self.username,         0, 1)
        grid.addWidget(QLabel("Password"),   1, 0)
        grid.addWidget(self.password,         1, 1)
        grid.addWidget(QLabel("Setup Code"), 2, 0)
        grid.addWidget(self.master,           2, 1)

        layout.addLayout(grid)

        btn = QPushButton("Create User")
        btn.setMinimumHeight(38)
        btn.clicked.connect(self.create)
        layout.addWidget(btn)

        self.setLayout(layout)

    def create(self):
        u = self.username.text().strip()
        p = self.password.text().strip()
        m = self.master.text().strip()

        if not u or not p or not m:
            QMessageBox.warning(self, "Error", "Please fill all fields.")
            return

        if not verify_master_code(m):
            QMessageBox.warning(self, "Error", "Invalid Setup Code ❌")
            return

        result = create_user(self.db_name, u, p)

        if result["success"]:
            self.qr = QRDisplay(result["secret"], result["qr_path"], result["recovery_codes"])
            self.login_window = LoginForm(self.db_name)
            self.qr.destroyed.connect(lambda: self.login_window.show())
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
#  DASHBOARD
# ──────────────────────────────────────────
class Dashboard(QWidget):

    def __init__(self, db_name, username="User"):
        super().__init__()
        self.db_name  = db_name

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

        app_name = QLabel("⚡ Evo Aura")
        app_name.setFont(QFont("Segoe UI", 14, QFont.Bold))
        app_name.setStyleSheet("color: #1a7fe8;")

        dash_title = QLabel("Dashboard")
        dash_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        dash_title.setAlignment(Qt.AlignCenter)
        dash_title.setStyleSheet("background: transparent;")

        user_label = QLabel(f"👤  {username}")
        user_label.setFont(QFont("Segoe UI", 11))

        logout_btn = QPushButton("Logout")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setFixedHeight(30)
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

        top_layout.addWidget(app_name)
        top_layout.addStretch()
        top_layout.addWidget(dash_title)
        top_layout.addStretch()
        top_layout.addWidget(user_label)
        top_layout.addWidget(logout_btn)

        main_layout.addWidget(top_frame)

        # ── MAIN CARD ──
        card = QFrame()
        card.setStyleSheet("background: white; border-radius: 14px; border: 1px solid #e6edf5;")

        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(50, 30, 50, 30)
        card_layout.setSpacing(20)

        welcome = QLabel(f"Welcome, {username} 👋")
        welcome.setAlignment(Qt.AlignCenter)
        welcome.setFont(QFont("Segoe UI", 22, QFont.Bold))
        welcome.setStyleSheet("color: #1a7fe8; background: transparent;")
        card_layout.addWidget(welcome)

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

        grid.addWidget(make_card_btn("⊞   Add Product",     "Add Product"), 0, 0)
        grid.addWidget(make_card_btn("🛒   Sale",            "Sale"),        0, 1)
        grid.addWidget(make_card_btn("👥   Users",           "Users"),       1, 0)
        grid.addWidget(make_card_btn("📊   Report Insights", "Report"),      1, 1)
        grid.addWidget(make_card_btn("🧾   Bill View",       "Bill View"),   2, 0, 1, 2)

        card_layout.addLayout(grid)
        card.setLayout(card_layout)
        main_layout.addWidget(card)

        self.setLayout(main_layout)

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