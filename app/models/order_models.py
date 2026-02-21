from pydantic import BaseModel, Field
from typing import List, Optional
from app.models.customer_models import CustomerCreateOrUseIn


class CartItemIn(BaseModel):
    item_code: str = Field(..., min_length=1)
    qty: float = Field(..., gt=0)


class PlaceOrderIn(CustomerCreateOrUseIn):
    cart: List[CartItemIn]
    notes: Optional[str] = ""