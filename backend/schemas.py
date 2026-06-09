"""
schemas.py - Pydantic schemas for request/response validation and serialization.
Each model group has Base (shared fields), Create (input), and Response (output) schemas.
"""

from typing import Optional, List
from pydantic import BaseModel


# ── Auth ─────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── User ─────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    is_active: bool

    model_config = {"from_attributes": True}


# ── Customer ──────────────────────────────────────────────────────────────────

class CustomerBase(BaseModel):
    name: str
    address: Optional[str] = ""
    customer_type: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(CustomerBase):
    is_active: Optional[bool] = True

class CustomerResponse(CustomerBase):
    id: int
    is_active: bool

    model_config = {"from_attributes": True}


# ── Item ──────────────────────────────────────────────────────────────────────

class ItemBase(BaseModel):
    code: str
    description: str
    unit_price: float = 0.0

class ItemCreate(ItemBase):
    pass

class ItemUpdate(ItemBase):
    is_active: Optional[bool] = True

class ItemResponse(ItemBase):
    id: int
    is_active: bool

    model_config = {"from_attributes": True}


# ── Invoice Line Items ────────────────────────────────────────────────────────

class InvoiceItemBase(BaseModel):
    item_code: str
    description: str
    quantity: float = 1.0
    unit_price: float = 0.0

class InvoiceItemResponse(InvoiceItemBase):
    id: int
    amount: float

    model_config = {"from_attributes": True}


# ── Invoice ───────────────────────────────────────────────────────────────────

class InvoiceBase(BaseModel):
    invoice_number: str
    invoice_date: str                          # "26/Feb/2026"
    customer_id: int
    customer_type: Optional[str] = ""
    destination: Optional[str] = ""
    currency: Optional[str] = "USD"
    payment_method: Optional[str] = "TT"
    shipping_method: Optional[str] = "N/A"
    reference: Optional[str] = ""
    freight: Optional[float] = 0.0
    notes: Optional[str] = "(Any Applicable Tax should be born by the Customer)"
    delivery_note: Optional[str] = ""
    status: Optional[str] = "draft"

class InvoiceCreate(InvoiceBase):
    line_items: List[InvoiceItemBase] = []

class InvoiceUpdate(InvoiceBase):
    line_items: List[InvoiceItemBase] = []

class InvoiceResponse(InvoiceBase):
    id: int
    goods_total: float
    invoice_total: float
    line_items: List[InvoiceItemResponse] = []
    customer: Optional[CustomerResponse] = None

    model_config = {"from_attributes": True}

class InvoiceSummary(BaseModel):
    """Lightweight invoice list item (no line items)."""
    id: int
    invoice_number: str
    invoice_date: str
    customer_id: int
    currency: str
    invoice_total: float
    status: str
    customer: Optional[CustomerResponse] = None

    model_config = {"from_attributes": True}


# ── Settings ──────────────────────────────────────────────────────────────────

class SettingsUpdate(BaseModel):
    """Dictionary of key→value pairs to update in settings."""
    settings: dict[str, str]

class SettingsResponse(BaseModel):
    settings: dict[str, str]


# ── Reports ───────────────────────────────────────────────────────────────────

class CustomerActivity(BaseModel):
    customer_id: int
    customer_name: str
    invoice_count: int
    total_amount: float

class ItemActivity(BaseModel):
    item_code: str
    description: str
    times_used: int
    total_quantity: float
    total_amount: float

class ReportResponse(BaseModel):
    customer_activity: List[CustomerActivity]
    item_activity: List[ItemActivity]
    total_invoices: int
    total_revenue: float
