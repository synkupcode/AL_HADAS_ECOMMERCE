# app/auth/otp.py

import time
import secrets
import hashlib
from typing import Dict

# ---------------------
# Configuration
# ---------------------
OTP_EXPIRY_SECONDS = 300
RESEND_COOLDOWN_SECONDS = 60
MAX_VERIFY_ATTEMPTS = 5

# ---------------------
# In-memory store
# ---------------------
_otp_store: Dict[str, dict] = {}

# ---------------------
# Helpers
# ---------------------
def _generate_otp() -> str:
    return f"{secrets.randbelow(1000000):06d}"

def _hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()

# ---------------------
# Create or reuse OTP
# ---------------------
def create_or_get_otp(identifier: str) -> str | None:

    now = time.time()
    record = _otp_store.get(identifier)

    if record and now < record["expires_at"]:
        return None

    otp = _generate_otp()

    _otp_store[identifier] = {
        "otp_hash": _hash_otp(otp),
        "otp_plain": otp,
        "created_at": now,
        "expires_at": now + OTP_EXPIRY_SECONDS,
        "attempts": 0
    }

    return otp

# ---------------------
# Verify OTP
# ---------------------
def verify_otp(identifier: str, otp: str) -> bool:

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

    del _otp_store[identifier]
    return True
