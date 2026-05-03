import pyotp

# The secret code shared with your phone app
SECRET_CODE = "JBSWY3DPEHPK3PXP"

def verify_step():
    # Initialize the TOTP logic
    totp = pyotp.totp.TOTP(SECRET_CODE)

    print("--- 2-STEP AUTHENTICATION ---")
    # Ask you for the code currently visible on your phone
    user_input = input("Enter the 6-digit code from your app: ").strip()

    # Confirm if the code matches
    if totp.verify(user_input):
        print("\nCONFIRMED: Access Granted! ✅")
    else:
        print("\nFAILED: Code is incorrect or expired. ❌")

if __name__ == "__main__":
    verify_step()
    