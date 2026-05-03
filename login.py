import sys
import sqlite3
import pyotp

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton,
    QLabel, QLineEdit, QGridLayout, QMessageBox
)

# 🔐 SECRET KEY (ADD SAME IN GOOGLE AUTHENTICATOR)
SECRET_CODE = "JBSWY3DPEHPK3PXP"


# ---------------- DATABASE SETUP ----------------
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    conn.commit()
    conn.close()


# ---------------- LOGIN WINDOW ----------------
class LoginForm(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Login Form')
        self.setFixedSize(400, 220)

        layout = QGridLayout()

        # USERNAME
        label_name = QLabel('Username')
        self.lineEdit_username = QLineEdit()
        self.lineEdit_username.setPlaceholderText('Enter username')

        layout.addWidget(label_name, 0, 0)
        layout.addWidget(self.lineEdit_username, 0, 1)

        # PASSWORD
        label_password = QLabel('Password')
        self.lineEdit_password = QLineEdit()
        self.lineEdit_password.setPlaceholderText('Enter password')
        self.lineEdit_password.setEchoMode(QLineEdit.Password)

        layout.addWidget(label_password, 1, 0)
        layout.addWidget(self.lineEdit_password, 1, 1)

        # BUTTONS
        button_login = QPushButton('Login')
        button_login.clicked.connect(self.check_login)

        button_signup = QPushButton('Signup')
        button_signup.clicked.connect(self.open_signup)

        layout.addWidget(button_login, 2, 0)
        layout.addWidget(button_signup, 2, 1)

        self.setLayout(layout)

    def check_login(self):
        username = self.lineEdit_username.text().strip()
        password = self.lineEdit_password.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter all fields")
            return

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        result = cursor.fetchone()
        conn.close()

        if result:
            QMessageBox.information(self, "Success", "Login Successful ✅")
        else:
            QMessageBox.warning(self, "Error", "Invalid Username or Password ❌")

    def open_signup(self):
        self.signup_window = SignupForm()
        self.signup_window.show()


# ---------------- SIGNUP WINDOW ----------------
class SignupForm(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Signup Form')
        self.setFixedSize(400, 260)

        layout = QGridLayout()

        # USERNAME
        label_name = QLabel('New Username')
        self.username = QLineEdit()
        self.username.setPlaceholderText('Create username')

        layout.addWidget(label_name, 0, 0)
        layout.addWidget(self.username, 0, 1)

        # PASSWORD
        label_password = QLabel('New Password')
        self.password = QLineEdit()
        self.password.setPlaceholderText('Create password')
        self.password.setEchoMode(QLineEdit.Password)

        layout.addWidget(label_password, 1, 0)
        layout.addWidget(self.password, 1, 1)

        # 🔐 OTP FIELD (REPLACED ADMIN KEY)
        label_super = QLabel('Enter 6-digit Code')
        self.super_password = QLineEdit()
        self.super_password.setPlaceholderText('Enter OTP from Authenticator')
        self.super_password.setEchoMode(QLineEdit.Password)

        layout.addWidget(label_super, 2, 0)
        layout.addWidget(self.super_password, 2, 1)

        # BUTTON
        button_create = QPushButton('Create Account')
        button_create.clicked.connect(self.create_account)

        layout.addWidget(button_create, 3, 0, 1, 2)

        self.setLayout(layout)

    def create_account(self):
        username = self.username.text().strip()
        password = self.password.text().strip()
        otp_code = self.super_password.text().strip()

        if not username or not password or not otp_code:
            QMessageBox.warning(self, "Error", "Please fill all fields")
            return

        # 🔐 VERIFY OTP
        totp = pyotp.TOTP(SECRET_CODE)

        if not totp.verify(otp_code):
            QMessageBox.warning(self, "Access Denied", "Invalid or Expired Code ❌")
            return

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            conn.commit()

            QMessageBox.information(self, "Success", "Account Created ✅")
            self.close()

        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "Username already exists")

        conn.close()


# ---------------- MAIN APP ----------------
if __name__ == '__main__':
    init_db()

    app = QApplication(sys.argv)

    form = LoginForm()
    form.show()

    sys.exit(app.exec_())