import tkinter as tk

root = tk.Tk()
root.title("Billing Software")

# ✅ Maximize window (not fullscreen)
root.state("zoomed")   # Windows only

# Background color
root.configure(bg="#2f4b7c")

# ========================
# CENTER FRAME (LOGIN BOX)
# ========================
center_frame = tk.Frame(root, bg="#2f4b7c")
center_frame.place(relx=0.5, rely=0.5, anchor="center")

# ========================
# TITLE
# ========================
title = tk.Label(
    center_frame,
    text="Billing Software",
    font=("Arial", 24, "bold"),
    bg="#2f4b7c",
    fg="white"
)
title.pack(pady=20)

# ========================
# USERNAME
# ========================
username = tk.Entry(
    center_frame,
    width=30,
    font=("Arial", 12),
    relief="solid",     # outline
    bd=2
)
username.insert(0, "Username")
username.pack(pady=10)

# ========================
# PASSWORD
# ========================
password = tk.Entry(
    center_frame,
    width=30,
    font=("Arial", 12),
    relief="solid",
    bd=2,
    show="*"
)
password.insert(0, "Password")
password.pack(pady=10)

# ========================
# LOGIN BUTTON
# ========================
login_btn = tk.Button(
    center_frame,
    text="Login",
    bg="#2ecc71",
    fg="white",
    width=25,
    relief="solid",  # outline
    bd=2
)
login_btn.pack(pady=10)

# ========================
# ADD USER BUTTON
# ========================
add_user_btn = tk.Button(
    center_frame,
    text="+ Add User",
    bg="#3498db",
    fg="white",
    width=25,
    relief="solid",
    bd=2
)
add_user_btn.pack(pady=10)

# ========================
# EXIT BUTTON (TOP RIGHT)
# ========================
exit_btn = tk.Button(
    root,
    text="❌ Exit",
    bg="red",
    fg="white",
    relief="solid",
    bd=2,
    command=root.destroy
)
exit_btn.place(relx=0.98, rely=0.02, anchor="ne")

# ========================
# BACK BUTTON (TOP LEFT)
# ========================
back_btn = tk.Button(
    root,
    text="⬅ Back",
    bg="#34495e",
    fg="white",
    relief="solid",
    bd=2,
    command=root.destroy
)
back_btn.place(relx=0.02, rely=0.02, anchor="nw")

root.mainloop()