import sys

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


# ---------------- DATABASE ----------------
def init_db(db_name="users.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT,
        otp_secret TEXT,
        recovery_codes TEXT
    )
    """)

    conn.commit()
    conn.close()


def has_users():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]

    conn.close()
    return count > 0


# ---------------- HELPERS ----------------
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


# ---------------- MASTER CODE ----------------
def verify_master_code(code):
    totp = pyotp.TOTP(MASTER_SECRET)
    return totp.verify(code)


# ---------------- USER CREATE ----------------
def create_user(username, password, role="user"):
    user_secret = pyotp.random_base32()
    recovery_codes = generate_recovery_codes()
    qr_path = generate_qr(user_secret, username)

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users VALUES (NULL, ?, ?, ?, ?, ?)",
            (username, password, role, user_secret, ",".join(recovery_codes))
        )
        conn.commit()

        return {
            "success": True,
            "secret": user_secret,
            "recovery_codes": recovery_codes,
            "qr_path": qr_path
        }

    except:
        return {"success": False, "message": "Username exists"}

    finally:
        conn.close()


# ---------------- LOGIN ----------------
def login_user(username, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT password, otp_secret, role FROM users WHERE username=?",
        (username,)
    )

    data = cursor.fetchone()
    conn.close()

    if not data:
        return {"success": False, "message": "User not found"}

    db_pass, secret, role = data

    if password != db_pass:
        return {"success": False, "message": "Wrong password"}

    return {
        "success": True,
        "secret": secret,
        "role": role
    }


# ---------------- VERIFY OTP ----------------
def verify_otp(secret, otp):
    return pyotp.TOTP(secret).verify(otp)


# ---------------- GET ADMIN SECRET ----------------
def get_admin_secret():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT otp_secret FROM users WHERE role='admin'")
    data = cursor.fetchone()

    conn.close()

    return data[0] if data else None


# ---------------- GET ALL USERNAMES ----------------
def get_all_usernames():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users ORDER BY username")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]


# ---------------- QR DISPLAY ----------------
class QRDisplay(QWidget):

    def __init__(self, secret, qr_path, recovery_codes):
        super().__init__()

        self.setWindowTitle("Setup 2FA")
        self.setFixedSize(420, 500)

        layout = QGridLayout()

        title = QLabel("Scan QR in Authenticator")
        title.setAlignment(Qt.AlignCenter)

        layout.addWidget(title, 0, 0, 1, 2)

        qr_label = QLabel()

        pixmap = QPixmap(qr_path)

        pixmap = pixmap.scaled(
            200,
            200,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        qr_label.setPixmap(pixmap)
        qr_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(qr_label, 1, 0, 1, 2)

        label_secret = QLabel(f"Secret:\n{secret}")
        label_secret.setWordWrap(True)

        layout.addWidget(label_secret, 2, 0, 1, 2)

        label_recovery = QLabel(
            "Recovery Codes:\n" + "\n".join(recovery_codes)
        )

        label_recovery.setWordWrap(True)

        layout.addWidget(label_recovery, 3, 0, 1, 2)

        btn_close = QPushButton("Done")
        btn_close.clicked.connect(self.close)

        layout.addWidget(btn_close, 4, 0, 1, 2)

        self.setLayout(layout)


# ---------------- STARTUP AUTH ----------------
class StartupAuth(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Security Check")
        self.setFixedSize(350, 150)

        layout = QGridLayout()

        self.otp_input = QLineEdit()

        self.otp_input.setPlaceholderText("Enter Setup Code")
        self.otp_input.setEchoMode(QLineEdit.Password)

        btn = QPushButton("Verify")
        btn.clicked.connect(self.verify)

        layout.addWidget(QLabel("Enter Setup Code"), 0, 0)
        layout.addWidget(self.otp_input, 0, 1)

        layout.addWidget(btn, 1, 0, 1, 2)

        self.setLayout(layout)

    def verify(self):

        if verify_master_code(self.otp_input.text().strip()):

            self.signup = SignupForm()
            self.signup.show()

            self.close()

        else:
            QMessageBox.warning(self, "Error", "Invalid Code ❌")


# ---------------- DASHBOARD ----------------
class Dashboard(QWidget):

    def __init__(self, username="Admin User"):
        super().__init__()

        self.setWindowTitle("Evo Aura Billing")
        self.showMaximized()

        # ================= MAIN LAYOUT =================
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(15)

        self.setStyleSheet("background-color: #f4f7fb;")

        # ================= TOP BAR =================
        top_frame = QFrame()
        top_frame.setFixedHeight(80)
        top_frame.setStyleSheet("""
            background: white;
            border-radius: 10px;
        """)

        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(20, 5, 20, 5)

        # -------- LEFT --------
        left_widget = QWidget()
        left_layout = QHBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        logo = QLabel()
        logo.setFixedSize(40, 40)

        pixmap = QPixmap("C:/Users/nawaz/Downloads/tkinker-billing-/seperate code/witness.png")

        logo.setPixmap(
            pixmap.scaled(
                logo.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )
        app_name = QLabel("Evo Aura")
        app_name.setFont(QFont("Segoe UI", 14, QFont.Bold))

        left_layout.addWidget(logo)
        left_layout.addWidget(app_name)

        # -------- CENTER (FIXED NO BG) --------
        title = QLabel("Dashboard")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)

        # 🔥 IMPORTANT FIX (no background box)
        title.setStyleSheet("background: transparent;")

        # Wrap for perfect centering
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.addStretch()
        title_layout.addWidget(title)
        title_layout.addStretch()

        # -------- RIGHT --------
        right_widget = QWidget()
        right_layout = QHBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        avatar = QLabel("👤")
        avatar.setStyleSheet("""
            font-size: 20px;
            background-color: #eef5ff;
            border-radius: 12px;
            padding: 5px;
        """)

        user_label = QLabel(username)
        user_label.setFont(QFont("Segoe UI", 11))

        logout_btn = QPushButton("Logout")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setFixedHeight(30)

        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff5c5c;
                color: white;
                border-radius: 6px;
                padding: 4px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff3b3b;
            }
        """)

        logout_btn.clicked.connect(self.close)

        right_layout.addWidget(avatar)
        right_layout.addWidget(user_label)
        right_layout.addWidget(logout_btn)

        # -------- ADD --------
        top_layout.addWidget(left_widget)
        top_layout.addWidget(title_container, 1)
        top_layout.addWidget(right_widget)

        main_layout.addWidget(top_frame)

        # ================= MAIN CARD =================
        card = QFrame()
        card.setStyleSheet("""
            background: white;
            border-radius: 14px;
            border: 1px solid #e6edf5;
        """)

        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(50, 30, 50, 30)
        card_layout.setSpacing(20)

        import os

        base_path = os.path.dirname(__file__)
        img_path = os.path.join(base_path, "C:/Users/nawaz/Downloads/tkinker-billing-/hloo_qr.png")

        # ================= WELCOME =================
        if os.path.exists(img_path):

            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(10)

            # ---- IMAGE ----
            img_label = QLabel()
            img_label.setFixedSize(100, 100)

            pixmap = QPixmap(img_path)
            if not pixmap.isNull():
                img_label.setPixmap(
                    pixmap.scaled(
                        img_label.size(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                )

            # ---- TEXT ----
            welcome = QLabel(f"Welcome, {username}")
            welcome.setFont(QFont("Segoe UI", 26, QFont.Bold))
            welcome.setStyleSheet("background: transparent;")

            # ---- LAYOUT (LEFT ↔ RIGHT) ----
            layout.addStretch()
            layout.addWidget(img_label)
            layout.addWidget(welcome)
            layout.addStretch()

            card_layout.addWidget(container)

        else:
            # 👉 ORIGINAL (UNCHANGED)
            welcome = QLabel(f"Welcome, {username}")
            welcome.setAlignment(Qt.AlignCenter)
            welcome.setFont(QFont("Segoe UI", 26, QFont.Bold))
            welcome.setStyleSheet("""
                QLabel {
                    background-color: #eef5ff;
                }
            """)

            card_layout.addWidget(welcome)


        # ================= BUTTON GRID =================
        grid = QGridLayout()
        grid.setSpacing(20)

        def create_btn(text, action):
            btn = QPushButton(text)
            btn.setMinimumHeight(120)

            btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    border: 1px solid #d6e4f0;
                    border-radius: 12px;
                    font-size: 18px;
                    font-weight: 600;
                    padding: 15px;
                }
                QPushButton:hover {
                    background-color: #f0f7ff;
                    border: 1px solid #4da3ff;
                }
            """)

            btn.clicked.connect(lambda: self.coming_soon(action))
            return btn

        grid.addWidget(create_btn("⊞   Add Product", "Add Product"), 0, 0)
        grid.addWidget(create_btn("🛒   Sale", "Sale"), 0, 1)
        grid.addWidget(create_btn("👥   Users", "Users"), 1, 0)
        grid.addWidget(create_btn("📊   Report\nInsights", "Report"), 1, 1)
        grid.addWidget(create_btn("🧾   Bill View", "Bill View"), 2, 0, 1, 2)

        card_layout.addLayout(grid)
        card.setLayout(card_layout)

        main_layout.addWidget(card)

        self.setLayout(main_layout)

    def coming_soon(self, page):
        QMessageBox.information(
            self,
            page,
            f"{page} Coming Soon 🚀"
        )
# ---------------- LOGIN ----------------
class LoginForm(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Login")
        self.setFixedSize(430, 270)

        layout = QGridLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- Username Dropdown ---
        self.username = QComboBox()
        self.username.setEditable(True)
        self.username.setInsertPolicy(QComboBox.NoInsert)
        self.username.setPlaceholderText("Select username  🡻")
        self.username.setMinimumHeight(34)
        self.username.setStyleSheet("""
            QComboBox {
                border: 2px solid #4da3ff;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 13px;
                background: white;
                color: #222;
            }
            QComboBox:hover {
                border: 2px solid #1a7fe8;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 32px;
                border-left: 1px solid #4da3ff;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                background-color: #eef5ff;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #4da3ff;
                border-radius: 4px;
                background: white;
                selection-background-color: #ddeeff;
                selection-color: #111;
                font-size: 13px;
                padding: 2px;
            }
        """)
        self.load_usernames()

        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setStyleSheet("""
            QLineEdit {
                border: 1px solid #c0d6ea;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 13px;
            }
        """)

        layout.addWidget(QLabel("Username"), 0, 0)
        layout.addWidget(self.username, 0, 1)

        layout.addWidget(QLabel("Password"), 1, 0)
        layout.addWidget(self.password, 1, 1)

        btn_login = QPushButton("Login")
        btn_login.clicked.connect(self.login)

        btn_signup = QPushButton("Signup")
        btn_signup.clicked.connect(self.open_signup)

        layout.addWidget(btn_login, 2, 0)
        layout.addWidget(btn_signup, 2, 1)

        self.setLayout(layout)

    def load_usernames(self):
        self.username.clear()
        usernames = get_all_usernames()
        for name in usernames:
            self.username.addItem(name)
        self.username.setCurrentIndex(-1)  # blank by default

    def login(self):

        u = self.username.currentText().strip()
        p = self.password.text().strip()

        result = login_user(u, p)

        if not result["success"]:
            QMessageBox.warning(
                self,
                "Error",
                result["message"]
            )
            return

        otp, ok = QInputDialog.getText(
            self,
            "2FA",
            "Enter OTP or Recovery Code:"
        )

        if ok:

            if verify_otp(result["secret"], otp):

                QMessageBox.information(
                    self,
                    "Success",
                    "Login Success ✅"
                )

                self.dashboard = Dashboard(u)
                self.dashboard.show()

                self.close()

                return


            if otp in result["recovery_codes"]:

                QMessageBox.information(
                    self,
                    "Success",
                    "Login via Recovery Code ✅"
                )

                return

            QMessageBox.warning(
                self,
                "Error",
                "Invalid Code ❌"
            )

    def open_signup(self):

        self.signup = SignupForm()
        self.signup.show()
        # Reload usernames when signup window closes
        self.signup.destroyed.connect(self.load_usernames)


# ---------------- SIGNUP ----------------
class SignupForm(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Signup")
        self.setFixedSize(430, 290)

        layout = QGridLayout()

        self.username = QLineEdit()

        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)

        self.master = QLineEdit()
        self.master.setEchoMode(QLineEdit.Password)

        layout.addWidget(QLabel("Username"), 0, 0)
        layout.addWidget(self.username, 0, 1)

        layout.addWidget(QLabel("Password"), 1, 0)
        layout.addWidget(self.password, 1, 1)

        layout.addWidget(QLabel("Setup Code"), 2, 0)
        layout.addWidget(self.master, 2, 1)

        btn = QPushButton("Create")
        btn.clicked.connect(self.create)

        layout.addWidget(btn, 3, 0, 1, 2)

        self.setLayout(layout)

    def create(self):

        u = self.username.text().strip()
        p = self.password.text().strip()
        m = self.master.text().strip()

        if not u or not p or not m:

            QMessageBox.warning(
                self,
                "Error",
                "Fill all fields"
            )

            return

        if not verify_master_code(m):

            QMessageBox.warning(
                self,
                "Error",
                "Invalid Setup Code"
            )

            return

        result = create_user(u, p)

        if result["success"]:

            self.qr = QRDisplay(
                result["secret"],
                result["qr_path"],
                result["recovery_codes"]
            )

            self.qr.show()

            self.close()

        else:

            QMessageBox.warning(
                self,
                "Error",
                result["message"]
            )


# ---------------- MAIN ----------------
if __name__ == "__main__":

    init_db()

    app = QApplication(sys.argv)

    if has_users():
        window = LoginForm()
    else:
        window = StartupAuth()

    window.show()

    sys.exit(app.exec_())
