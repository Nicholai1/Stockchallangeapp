# app/utils/test_auth.py
from auth import get_password_hash
from passlib.context import CryptContext

# Hvis du ikke allerede har pwd_context i auth.py, kan du definere det her midlertidigt:
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def test_password_hashing(password: str):
    """
    Hash a password safely with truncation for bcrypt and print result.
    """
    # Truncate to 72 bytes to avoid bcrypt limitation
    truncated = password.encode("utf-8")[:72]
    hashed = pwd_context.hash(truncated)
    print(f"Password: {password} -> Hashed: {hashed}")

if __name__ == "__main__":
    test_passwords = [
        "1234567",
        "Hemmelig",
        "a" * 100,  # test long password
        "P@$$w0rd_with_special_chars!",
        "😀🔒🚀" * 10  # test unicode/emojis
    ]

    for pw in test_passwords:
        try:
            test_password_hashing(pw)
        except Exception as e:
            print(f"FAILED: {pw} -> {e}")