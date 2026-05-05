import sys
import sqlite3
import pyotp
import qrcode
import random
import string

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton,
    QLabel, QLineEdit, QGridLayout,
    QMessageBox, QInputDialog, QVBoxLayout, QHBoxLayout
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal

# 🔐 MASTER SECRET
MASTER_SECRET = "KRSXG5DSNFXGOIDB"


# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        otp_secret TEXT,
        qr_path TEXT,
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
        for _ in range(3)
    ]


def generate_qr(secret, username):
    uri = pyotp.TOTP(secret).provisioning_uri(
        name=username,
        issuer_name="SecureApp"
    )
    img = qrcode.make(uri)
    path = f"{username}_qr.png"
    img.save(path)
    return path


# ---------------- CLICKABLE LABEL ----------------
class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        self.clicked.emit()


# ---------------- QR DISPLAY ----------------
class QRDisplay(QWidget):
    def __init__(self, username, secret, qr_path, recovery_codes):
        super().__init__()

        self.username = username
        self.secret = secret

        self.setWindowTitle("Setup 2FA")
        self.setFixedSize(420, 520)

        layout = QVBoxLayout()

        title = QLabel("📱 Scan QR in Authenticator")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # QR
        qr_label = QLabel()
        pixmap = QPixmap(qr_path).scaled(240, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        qr_label.setPixmap(pixmap)
        qr_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(qr_label)

        # SECRET + COPY
        secret_layout = QHBoxLayout()

        self.secret_field = QLineEdit(secret)
        self.secret_field.setReadOnly(True)

        btn_copy = QPushButton("Copy")
        btn_copy.clicked.connect(self.copy_secret)

        secret_layout.addWidget(self.secret_field)
        secret_layout.addWidget(btn_copy)

        layout.addLayout(secret_layout)

        # 🔹 Forgot link
        forgot = ClickableLabel("<a href='#'>Forgot Code?</a>")
        forgot.setAlignment(Qt.AlignRight)
        forgot.setTextFormat(Qt.RichText)
        forgot.clicked.connect(self.open_recovery)
        layout.addWidget(forgot)

        # Recovery codes
        rec_text = "\n".join(recovery_codes)
        rec_label = QLabel("Recovery Codes:\n" + rec_text)
        rec_label.setWordWrap(True)
        layout.addWidget(rec_label)

        btn_close = QPushButton("Done")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)

        self.setLayout(layout)

    def copy_secret(self):
        QApplication.clipboard().setText(self.secret)
        QMessageBox.information(self, "Copied", "Secret copied ✅")

    def open_recovery(self):
        username, ok = QInputDialog.getText(self, "Recover", "Enter Username:")
        if ok and username:
            self.recovery = RecoveryAuth(username)
            self.recovery.show()


# ---------------- RECOVERY ----------------
class RecoveryAuth(QWidget):
    def __init__(self, username):
        super().__init__()

        self.username = username

        self.setWindowTitle("Recover 2FA")
        self.setFixedSize(350, 150)

        layout = QGridLayout()

        self.master_input = QLineEdit()
        self.master_input.setEchoMode(QLineEdit.Password)

        btn = QPushButton("Verify")
        btn.clicked.connect(self.verify)

        layout.addWidget(QLabel("Master Code"), 0, 0)
        layout.addWidget(self.master_input, 0, 1)
        layout.addWidget(btn, 1, 0, 1, 2)

        self.setLayout(layout)

    def verify(self):
        if pyotp.TOTP(MASTER_SECRET).verify(self.master_input.text().strip()):
            self.show_qr()
            self.close()
        else:
            QMessageBox.warning(self, "Error", "Invalid Code ❌")

    def show_qr(self):
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT otp_secret, qr_path, recovery_codes FROM users WHERE username=?",
            (self.username,)
        )

        data = cursor.fetchone()
        conn.close()

        if data:
            secret, qr_path, recovery = data
            self.qr = QRDisplay(self.username, secret, qr_path, recovery.split(","))
            self.qr.show()
        else:
            QMessageBox.warning(self, "Error", "User not found")


# ---------------- LOGIN ----------------
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
        u = self.username.text().strip()
        p = self.password.text().strip()

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT password, otp_secret, recovery_codes FROM users WHERE username=?",
            (u,)
        )

        data = cursor.fetchone()
        conn.close()

        if not data:
            QMessageBox.warning(self, "Error", "User not found")
            return

        db_pass, secret, recovery = data

        if p != db_pass:
            QMessageBox.warning(self, "Error", "Wrong Password")
            return

        otp, ok = QInputDialog.getText(self, "2FA", "Enter OTP or Recovery Code:")

        if ok:
            totp = pyotp.TOTP(secret)

            if totp.verify(otp):
                QMessageBox.information(self, "Success", "Login Success ✅")
                return

            if otp in recovery.split(","):
                QMessageBox.information(self, "Success", "Login via Recovery Code ✅")
                return

            QMessageBox.warning(self, "Error", "Invalid Code ❌")

    def open_signup(self):
        self.signup = SignupForm()
        self.signup.show()


# ---------------- SIGNUP ----------------
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
        u = self.username.text().strip()
        p = self.password.text().strip()
        m = self.master.text().strip()

        if not u or not p or not m:
            QMessageBox.warning(self, "Error", "Fill all fields")
            return

        if not pyotp.TOTP(MASTER_SECRET).verify(m):
            QMessageBox.warning(self, "Error", "Invalid Setup Code")
            return

        user_secret = pyotp.random_base32()
        recovery_codes = generate_recovery_codes()
        qr_path = generate_qr(user_secret, u)

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users VALUES (NULL, ?, ?, ?, ?, ?)",
                (u, p, user_secret, qr_path, ",".join(recovery_codes))
            )
            conn.commit()

            self.qr = QRDisplay(u, user_secret, qr_path, recovery_codes)
            self.qr.show()

            self.close()

        except:
            QMessageBox.warning(self, "Error", "Username exists")

        conn.close()


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