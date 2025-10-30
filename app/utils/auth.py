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


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    pw_bytes = plain_password.encode("utf-8")
    if len(pw_bytes) > 72:
        pw_bytes = pw_bytes[:72]
    return pwd_context.verify(pw_bytes, hashed_password)