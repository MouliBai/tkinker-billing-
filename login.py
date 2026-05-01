import sys
import sqlite3  # Used to connect SQLite database

# Import PyQt5 widgets
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton,
    QLabel, QLineEdit, QGridLayout, QMessageBox
)

# ---------------- DATABASE SETUP ----------------
def init_db():
    """Create database and table if not exists"""
    conn = sqlite3.connect("users.db")  # Create/connect DB file
    cursor = conn.cursor()

    # Create table
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

        # Window settings
        self.setWindowTitle('Login Form')
        self.setFixedSize(400, 220)  # Slight height increase

        # Create layout
        layout = QGridLayout()

        # -------- USERNAME --------
        label_name = QLabel('Username')
        self.lineEdit_username = QLineEdit()
        self.lineEdit_username.setPlaceholderText('Enter username')

        layout.addWidget(label_name, 0, 0)
        layout.addWidget(self.lineEdit_username, 0, 1)

        # -------- PASSWORD --------
        label_password = QLabel('Password')
        self.lineEdit_password = QLineEdit()
        self.lineEdit_password.setPlaceholderText('Enter password')
        self.lineEdit_password.setEchoMode(QLineEdit.Password)  # Hide password

        layout.addWidget(label_password, 1, 0)
        layout.addWidget(self.lineEdit_password, 1, 1)

        # -------- LOGIN BUTTON --------
        button_login = QPushButton('Login')
        button_login.clicked.connect(self.check_login)

        # -------- SIGNUP BUTTON --------
        button_signup = QPushButton('Signup')
        button_signup.clicked.connect(self.open_signup)

        # Add buttons
        layout.addWidget(button_login, 2, 0)
        layout.addWidget(button_signup, 2, 1)

        self.setLayout(layout)

    # -------- LOGIN FUNCTION --------
    def check_login(self):
        username = self.lineEdit_username.text().strip()
        password = self.lineEdit_password.text().strip()

        # Validation
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
            QMessageBox.information(self, "Success", "Login Successful")
        else:
            QMessageBox.warning(self, "Error", "Invalid Username or Password")

    # -------- OPEN SIGNUP WINDOW --------
    def open_signup(self):
        self.signup_window = SignupForm()
        self.signup_window.show()


# ---------------- SIGNUP WINDOW ----------------
class SignupForm(QWidget):
    def __init__(self):
        super().__init__()

        # Window settings
        self.setWindowTitle('Signup Form')
        self.setFixedSize(400, 260)  # Increased height for new field

        # Layout
        layout = QGridLayout()

        # -------- USERNAME --------
        label_name = QLabel('New Username')
        self.username = QLineEdit()
        self.username.setPlaceholderText('Create username')

        layout.addWidget(label_name, 0, 0)
        layout.addWidget(self.username, 0, 1)

        # -------- PASSWORD --------
        label_password = QLabel('New Password')
        self.password = QLineEdit()
        self.password.setPlaceholderText('Create password')
        self.password.setEchoMode(QLineEdit.Password)

        layout.addWidget(label_password, 1, 0)
        layout.addWidget(self.password, 1, 1)

        # -------- SUPER PASSWORD (NEW) --------
        label_super = QLabel('Admin Key')
        self.super_password = QLineEdit()
        self.super_password.setPlaceholderText('Enter admin key')
        self.super_password.setEchoMode(QLineEdit.Password)

        layout.addWidget(label_super, 2, 0)
        layout.addWidget(self.super_password, 2, 1)

        # -------- CREATE BUTTON --------
        button_create = QPushButton('Create Account')
        button_create.clicked.connect(self.create_account)

        layout.addWidget(button_create, 3, 0, 1, 2)

        self.setLayout(layout)

        # 🔐 SUPER PASSWORD (CHANGE THIS VALUE)
        self.ADMIN_KEY = "admin123"

    # -------- CREATE ACCOUNT FUNCTION --------
    def create_account(self):
        username = self.username.text().strip()
        password = self.password.text().strip()
        super_pass = self.super_password.text().strip()

        # Check empty fields
        if not username or not password or not super_pass:
            QMessageBox.warning(self, "Error", "Please fill all fields")
            return

        # 🔐 CHECK ADMIN KEY FIRST
        if super_pass != self.ADMIN_KEY:
            QMessageBox.warning(self, "Access Denied", "Invalid Admin Key")
            return

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            conn.commit()

            QMessageBox.information(self, "Success", "Account Created")
            self.close()

        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "Username already exists")

        conn.close()


# ---------------- MAIN APP ----------------
if __name__ == '__main__':
    init_db()  # Create DB first

    app = QApplication(sys.argv)

    form = LoginForm()
    form.show()

    sys.exit(app.exec_())