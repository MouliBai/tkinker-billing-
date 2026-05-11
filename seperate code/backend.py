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