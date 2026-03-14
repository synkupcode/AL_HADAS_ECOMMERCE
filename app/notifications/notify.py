# app/api/auth.py
from fastapi import APIRouter, Response, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr

from app.notifications.notify import send_otp as otp_sender, verify_otp as otp_verifier
from app.auth.jwt import create_access_token, create_refresh_token

router = APIRouter(prefix="/api/auth", tags=["Auth"])

class OTPRequest(BaseModel):
    email: EmailStr

@router.post("/request-otp")
async def request_otp(payload: OTPRequest, background_tasks: BackgroundTasks):
    """
    Sends OTP to email immediately using BackgroundTasks.
    """
    return otp_sender(payload.email, background_tasks)

class OTPVerify(BaseModel):
    email: EmailStr
    code: str

@router.post("/verify-otp")
def verify_otp_endpoint(payload: OTPVerify, response: Response):
    result = otp_verifier(payload.email, payload.code)
    if result["status"] != "verified":
        raise HTTPException(status_code=400, detail="Invalid OTP")

    access_token = create_access_token({"sub": payload.email})
    refresh_token = create_refresh_token({"sub": payload.email})

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="none"
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none"
    )

    return {"message": "Login successful"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}
