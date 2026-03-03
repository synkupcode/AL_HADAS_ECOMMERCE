from fastapi import APIRouter, Response, Request, HTTPException
from pydantic import BaseModel, EmailStr

from app.notifications.notify import send_otp, verify_otp
from app.auth.jwt import create_access_token, create_refresh_token

router = APIRouter(prefix="/api/auth", tags=["Auth"])


class OTPRequest(BaseModel):
    email: EmailStr


@router.post("/request-otp")
def request_otp(payload: OTPRequest):
    return send_otp(payload.email)


class OTPVerify(BaseModel):
    email: EmailStr
    code: str


@router.post("/verify-otp")
def verify_otp_endpoint(payload: OTPVerify, response: Response):

    result = verify_otp(payload.email, payload.code)

    if result["status"] != "verified":
        raise HTTPException(status_code=400, detail="Invalid OTP")

    access_token = create_access_token({"sub": payload.email})
    refresh_token = create_refresh_token({"sub": payload.email})

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax"
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax"
    )

    return {"message": "Login successful"}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}
