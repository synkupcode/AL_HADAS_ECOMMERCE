
from pydantic import BaseModel, Field
from typing import Optional


class AddressIn(BaseModel):
    address_line1: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    address_type: Optional[str] = "Billing"

    # Extra fields for your E-Commerce RFQ snapshot (optional)
    building_no: Optional[str] = None
    street_name: Optional[str] = None
    district: Optional[str] = None
    full_address: Optional[str] = None


class ContactIn(BaseModel):
    first_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class CustomerCreateOrUseIn(BaseModel):
    phone: str = Field(..., min_length=3)

    # Required if new customer
    customer_name: Optional[str] = None
    customer_type: Optional[str] = "Individual"
    vat_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[AddressIn] = None
    contact: Optional[ContactIn] = None

    # Optional business fields
    cr_no: Optional[str] = None
    company_name: Optional[str] = None
