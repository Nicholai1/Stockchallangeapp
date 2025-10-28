# app/utils/auth.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """
    Hash a password safely with bcrypt, truncating at 72 bytes if necessary.
    """
    # Encode password til bytes
    pw_bytes = password.encode("utf-8")

    # Truncate til max 72 bytes (bcrypt begrænsning)
    if len(pw_bytes) > 72:
        pw_bytes = pw_bytes[:72]

    # Hash password direkte fra bytes
    return pwd_context.hash(pw_bytes)