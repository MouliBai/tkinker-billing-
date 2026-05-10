"""
========================================================
🔐 EVO AURA BILLING SYSTEM (WITH 2FA)
--------------------------------------------------------
Flow:
1. App starts
2. Check if users exist
3. If NO → StartupAuth (Master Code)
4. If YES → Login
5. After login → OTP Verification
6. Success → Dashboard
7. Signup → QR + Recovery Codes
========================================================
"""

import sys
import os

# ---------------- PYQT IMPORTS ----------------
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel,
    QLineEdit, QGridLayout, QMessageBox,
    QInputDialog, QVBoxLayout, QHBoxLayout, QFrame
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt

# ---------------- BACKEND IMPORT ----------------
from backend import *


# ========================================================
# 🔹 QR DISPLAY WINDOW (Shown after signup)
# ========================================================
class QRDisplay(QWidget):
    def __init__(self, secret, qr_path, recovery_codes):
        super().__init__()

        self.setWindowTitle("Setup 2FA")
        self.setFixedSize(420, 500)

        layout = QGridLayout()

        # Title
        title = QLabel("Scan QR in Authenticator")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title, 0, 0, 1, 2)

        # QR Image
        qr_label = QLabel()
        pixmap = QPixmap(qr_path)

        qr_label.setPixmap(
            pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        qr_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(qr_label, 1, 0, 1, 2)

        # Secret Key
        layout.addWidget(QLabel(f"Secret:\n{secret}"), 2, 0, 1, 2)

        # Recovery Codes
        layout.addWidget(
            QLabel("Recovery Codes:\n" + "\n".join(recovery_codes)),
            3, 0, 1, 2
        )

        # Done Button
        btn_close = QPushButton("Done")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close, 4, 0, 1, 2)

        self.setLayout(layout)


# ========================================================
# 🔹 FIRST TIME AUTH (Master Code Screen)
# ========================================================
class StartupAuth(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Security Check")
        self.setFixedSize(350, 150)

        layout = QGridLayout()

        # Input field
        self.otp_input = QLineEdit()
        self.otp_input.setPlaceholderText("Enter Setup Code")
        self.otp_input.setEchoMode(QLineEdit.Password)

        # Verify Button
        btn = QPushButton("Verify")
        btn.clicked.connect(self.verify)

        layout.addWidget(QLabel("Enter Setup Code"), 0, 0)
        layout.addWidget(self.otp_input, 0, 1)
        layout.addWidget(btn, 1, 0, 1, 2)

        self.setLayout(layout)

    def verify(self):
        """Check master setup code"""

        if verify_master_code(self.otp_input.text().strip()):
            self.signup = SignupForm()
            self.signup.show()
            self.close()
        else:
            QMessageBox.warning(self, "Error", "Invalid Code ❌")


# ========================================================
# 🔹 DASHBOARD (Main App Screen)
# ========================================================
class Dashboard(QWidget):
    def __init__(self, username="Admin"):
        super().__init__()

        self.setWindowTitle("Evo Aura Billing")
        self.showMaximized()

        main_layout = QVBoxLayout()
        self.setStyleSheet("background-color: #f4f7fb;")

        # ---------------- TOP BAR ----------------
        top_frame = self.create_top_bar(username)
        main_layout.addWidget(top_frame)

        # ---------------- MAIN CARD ----------------
        card = self.create_main_card(username)
        main_layout.addWidget(card)

        self.setLayout(main_layout)

    # ---------- TOP BAR ----------
    def create_top_bar(self, username):
        frame = QFrame()
        frame.setFixedHeight(80)
        frame.setStyleSheet("background: white; border-radius: 10px;")

        layout = QHBoxLayout(frame)

        # Left (Logo + Name)
        left = QLabel("Evo Aura")
        left.setFont(QFont("Segoe UI", 14, QFont.Bold))

        # Center (Title)
        title = QLabel("Dashboard")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)

        # Right (User + Logout)
        logout = QPushButton("Logout")
        logout.clicked.connect(self.close)

        layout.addWidget(left)
        layout.addStretch()
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(QLabel(username))
        layout.addWidget(logout)

        return frame

    # ---------- MAIN CARD ----------
    def create_main_card(self, username):
        card = QFrame()
        card.setStyleSheet("background: white; border-radius: 14px;")

        layout = QVBoxLayout()

        # Welcome
        welcome = QLabel(f"Welcome, {username}")
        welcome.setFont(QFont("Segoe UI", 26, QFont.Bold))
        welcome.setAlignment(Qt.AlignCenter)

        layout.addWidget(welcome)

        # Buttons Grid
        grid = QGridLayout()

        def create_btn(text):
            btn = QPushButton(text)
            btn.setMinimumHeight(100)
            btn.clicked.connect(lambda: self.coming_soon(text))
            return btn

        grid.addWidget(create_btn("Add Product"), 0, 0)
        grid.addWidget(create_btn("Sale"), 0, 1)
        grid.addWidget(create_btn("Users"), 1, 0)
        grid.addWidget(create_btn("Reports"), 1, 1)

        layout.addLayout(grid)
        card.setLayout(layout)

        return card

    def coming_soon(self, page):
        QMessageBox.information(self, page, f"{page} Coming Soon 🚀")


# ========================================================
# 🔹 LOGIN SCREEN
# ========================================================
class LoginForm(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Login")
        self.setFixedSize(400, 220)

        layout = QGridLayout()

        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)

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

    def login(self):
        """Handle login + OTP verification"""

        u = self.username.text().strip()
        p = self.password.text().strip()

        result = login_user(u, p)

        if not result["success"]:
            QMessageBox.warning(self, "Error", result["message"])
            return

        # OTP Prompt
        otp, ok = QInputDialog.getText(self, "2FA", "Enter OTP:")

        if ok and verify_otp(result["secret"], otp):
            QMessageBox.information(self, "Success", "Login Success ✅")

            self.dashboard = Dashboard(u)
            self.dashboard.show()
            self.close()
        else:
            QMessageBox.warning(self, "Error", "Invalid Code ❌")

    def open_signup(self):
        self.signup = SignupForm()
        self.signup.show()


# ========================================================
# 🔹 SIGNUP SCREEN
# ========================================================
class SignupForm(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Signup")
        self.setFixedSize(400, 260)

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
        """Create user + generate QR"""

        u = self.username.text().strip()
        p = self.password.text().strip()
        m = self.master.text().strip()

        if not u or not p or not m:
            QMessageBox.warning(self, "Error", "Fill all fields")
            return

        if not verify_master_code(m):
            QMessageBox.warning(self, "Error", "Invalid Setup Code")
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
            QMessageBox.warning(self, "Error", result["message"])


# ========================================================
# 🚀 MAIN ENTRY POINT
# ========================================================
if __name__ == "__main__":

    init_db()  # Create DB if not exists

    app = QApplication(sys.argv)

    # Check if users exist
    if has_users():
        window = LoginForm()
    else:
        window = StartupAuth()

    window.show()

    sys.exit(app.exec_())