from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.services.profile_service import get_profile, update_profile

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("/me")
def profile_me(current_user=Depends(get_current_user)):
    email = current_user["sub"]
    return get_profile(email)


@router.put("/update")
def profile_update(payload: dict, current_user=Depends(get_current_user)):
    email = current_user["sub"]
    return update_profile(email, payload)
