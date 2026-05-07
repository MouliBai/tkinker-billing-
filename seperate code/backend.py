import sqlite3
import pyotp
import qrcode
import random
import string

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


# ---------------- AUTH ----------------
def verify_master_code(code):
    totp = pyotp.TOTP(MASTER_SECRET)
    return totp.verify(code)


def create_user(username, password):

    user_secret = pyotp.random_base32()

    recovery_codes = generate_recovery_codes()

    qr_path = generate_qr(user_secret, username)

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users VALUES (NULL, ?, ?, ?, ?)",
            (
                username,
                password,
                user_secret,
                ",".join(recovery_codes)
            )
        )

        conn.commit()

        return {
            "success": True,
            "secret": user_secret,
            "recovery_codes": recovery_codes,
            "qr_path": qr_path
        }

    except:
        return {
            "success": False,
            "message": "Username already exists"
        }

    finally:
        conn.close()


def login_user(username, password):

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT password, otp_secret, recovery_codes FROM users WHERE username=?",
        (username,)
    )

    data = cursor.fetchone()

    conn.close()

    if not data:
        return {
            "success": False,
            "message": "User not found"
        }

    db_pass, secret, recovery = data

    if password != db_pass:
        return {
            "success": False,
            "message": "Wrong password"
        }

    return {
        "success": True,
        "secret": secret,
        "recovery_codes": recovery.split(",")
    }


def verify_otp(secret, otp):
    totp = pyotp.TOTP(secret)
    return totp.verify(otp)