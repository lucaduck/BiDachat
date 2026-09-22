import base64
import binascii
import hashlib
import hmac
import secrets

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_KEY_LENGTH = 64
PASSWORD_SALT_BYTES = 16
SESSION_TOKEN_BYTES = 32


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password must not be empty")

    salt = secrets.token_bytes(PASSWORD_SALT_BYTES)
    password_hash = _derive_password_hash(password, salt)
    encoded_salt = base64.urlsafe_b64encode(salt).decode("ascii")
    encoded_hash = base64.urlsafe_b64encode(password_hash).decode("ascii")
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${encoded_salt}${encoded_hash}"


def verify_password(password: str, encoded_password_hash: str) -> bool:
    try:
        algorithm, n, r, p, encoded_salt, encoded_hash = encoded_password_hash.split(
            "$"
        )
        if algorithm != "scrypt":
            return False
        if (int(n), int(r), int(p)) != (SCRYPT_N, SCRYPT_R, SCRYPT_P):
            return False
        salt = base64.urlsafe_b64decode(encoded_salt.encode("ascii"))
        expected_hash = base64.urlsafe_b64decode(encoded_hash.encode("ascii"))
    except (binascii.Error, ValueError, UnicodeEncodeError):
        return False

    actual_hash = _derive_password_hash(password, salt)
    return hmac.compare_digest(actual_hash, expected_hash)


def generate_session_token() -> str:
    return secrets.token_urlsafe(SESSION_TOKEN_BYTES)


def hash_session_token(token: str) -> str:
    if not token:
        raise ValueError("Session token must not be empty")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _derive_password_hash(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=SCRYPT_KEY_LENGTH,
    )
