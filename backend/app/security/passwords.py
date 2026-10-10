"""Password hashing (Argon2id) and the password policy."""
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_hasher = PasswordHasher()  # Argon2id with the library's current recommended parameters

MIN_LENGTH = 10
MAX_LENGTH = 128

# A real hash of a throwaway value. Verifying against it when the email is unknown
# keeps response time similar whether or not the account exists.
_DUMMY_HASH = _hasher.hash("not-a-real-password-for-timing-only")


def validate_password_policy(password: str, email: str | None = None) -> list[str]:
    """Return human-readable problems; an empty list means the password is acceptable."""
    problems: list[str] = []
    if len(password) < MIN_LENGTH:
        problems.append(f"Use at least {MIN_LENGTH} characters.")
    if len(password) > MAX_LENGTH:
        problems.append(f"Use at most {MAX_LENGTH} characters.")
    if password.strip() == "":
        problems.append("Password cannot be only spaces.")
    if email and password.lower() == email.lower():
        problems.append("Password cannot be the same as your email.")
    return problems


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    """Constant-effort verification. Pass None for unknown users."""
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)
