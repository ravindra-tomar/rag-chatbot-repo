from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import secrets

from jose import JWTError, jwt

from app.core.config import settings

ALGORITHM = "HS256"
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(
        password.encode(), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P
    )
    encoded_salt = base64.urlsafe_b64encode(salt).decode()
    encoded_hash = base64.urlsafe_b64encode(derived).decode()
    return f"scrypt${encoded_salt}${encoded_hash}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        scheme, encoded_salt, encoded_hash = password_hash.split("$", 2)
        if scheme != "scrypt":
            return False
        salt = base64.urlsafe_b64decode(encoded_salt.encode())
        expected = base64.urlsafe_b64decode(encoded_hash.encode())
        actual = hashlib.scrypt(
            password.encode(), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int) -> str:
    expires = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode({"sub": str(user_id), "exp": expires}, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_user_id(token: str) -> int:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise ValueError("Invalid token")
        return int(user_id)
    except (JWTError, ValueError, TypeError) as exc:
        raise ValueError("Invalid or expired token") from exc