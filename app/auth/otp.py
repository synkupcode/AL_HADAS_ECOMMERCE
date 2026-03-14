
import time
import secrets
import hashlib
from typing import Dict

# ---------------------
# Configuration
# ---------------------
OTP_EXPIRY_SECONDS = 300          # 5 minutes
RESEND_COOLDOWN_SECONDS = 60      # 1 minute between resend requests
MAX_VERIFY_ATTEMPTS = 5

# ---------------------
# In-memory OTP store
# ---------------------
_otp_store: Dict[str, dict] = {}


# ---------------------
# Internal Helpers
# ---------------------
def _generate_otp() -> str:
    return f"{secrets.randbelow(1000000):06d}"


def _hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()


# ---------------------
# Public Functions
# ---------------------
def create_or_get_otp(identifier: str) -> str:
    """
    Returns the OTP to send.
    If existing OTP is valid, returns the same OTP (for resend behavior).
    """
    now = time.time()
    record = _otp_store.get(identifier)

    if record and now < record["expires_at"]:
        return record["otp_plain"]  # reuse existing OTP

    otp = _generate_otp()
    _otp_store[identifier] = {
        "otp_hash": _hash_otp(otp),
        "otp_plain": otp,
        "created_at": now,
        "expires_at": now + OTP_EXPIRY_SECONDS,
        "attempts": 0
    }

    return otp


def can_resend(identifier: str) -> bool:
    """
    Returns True if cooldown has passed or no OTP exists.
    """
    record = _otp_store.get(identifier)
    if not record:
        return True
    return (time.time() - record["created_at"]) >= RESEND_COOLDOWN_SECONDS


def verify_otp(identifier: str, otp: str) -> bool:
    """
    Verifies OTP. Returns True if correct and valid, False otherwise.
    Deletes OTP on success, expiry, or too many attempts.
    """
    record = _otp_store.get(identifier)
    if not record:
        return False

    now = time.time()

    if now > record["expires_at"]:
        del _otp_store[identifier]
        return False

    if record["attempts"] >= MAX_VERIFY_ATTEMPTS:
        del _otp_store[identifier]
        return False

    if record["otp_hash"] != _hash_otp(otp):
        record["attempts"] += 1
        return False

    # Successful verification
    del _otp_store[identifier]
    return True
