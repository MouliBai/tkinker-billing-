import sys

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QLabel,
    QLineEdit,
    QGridLayout,
    QMessageBox,
    QInputDialog
)

from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from backend import *


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