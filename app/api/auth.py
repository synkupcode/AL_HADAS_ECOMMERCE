# app/api/auth.py

from fastapi import APIRouter, Response, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr

from app.notifications.notify import send_otp as otp_sender, verify_otp as otp_verifier
from app.auth.jwt import create_access_token, create_refresh_token

router = APIRouter(prefix="/api/auth", tags=["Auth"])


# -------------------------
# Request OTP Payload
# -------------------------
class OTPRequest(BaseModel):
    email: EmailStr


@router.post("/request-otp")
def request_otp(payload: OTPRequest, background_tasks: BackgroundTasks):
    """
    Sends OTP to the provided email.
    Resends same OTP if still valid (5 min validity, 1 min cooldown).

    Uses background task to avoid blocking API response for SMTP.
    """
    # Schedule OTP sending in background
    background_tasks.add_task(otp_sender, payload.email)

    # Determine current OTP status for frontend UI
    # send_otp returns {"status": ..., "message": ...}
    result = otp_sender(payload.email)

    return result


# -------------------------
# Verify OTP Payload
# -------------------------
class OTPVerify(BaseModel):
    email: EmailStr
    code: str


@router.post("/verify-otp")
def verify_otp_endpoint(payload: OTPVerify, response: Response):
    """
    Verifies OTP and issues access & refresh tokens.
    Sets secure HttpOnly cookies for frontend.
    """
    result = otp_verifier(payload.email, payload.code)

    if result["status"] != "verified":
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Generate JWT tokens
    access_token = create_access_token({"sub": payload.email})
    refresh_token = create_refresh_token({"sub": payload.email})

    # Set secure cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,      # ✅ REQUIRED for HTTPS
        samesite="none"   # ✅ REQUIRED for cross-domain
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none"
    )

    return {"message": "Login successful"}


# -------------------------
# Logout Endpoint
# -------------------------
@router.post("/logout")
def logout(response: Response):
    """
    Clears authentication cookies on logout.
    """
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}
