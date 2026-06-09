"""
models.py - SQLAlchemy ORM models for the BLS Invoice application.
Defines all database tables: Users, Customers, Items, Invoices, InvoiceItems,
and Settings (company info + bank details stored as key-value pairs).
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime,
    Boolean, ForeignKey
)
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    """Application user with hashed password for login authentication."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Customer(Base):
    """Customer/client record. Address is stored as free text."""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    address = Column(Text, nullable=True)       # Multi-line address
    customer_type = Column(String(50), default="")  # e.g. EXPORT, LOCAL
    email = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Back-reference to invoices for reporting
    invoices = relationship("Invoice", back_populates="customer")


class Item(Base):
    """Product/service catalog item with a default price."""
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    unit_price = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Invoice(Base):
    """
    Invoice header record. Line items are stored separately in InvoiceItem.
    The invoice number is a free-format string (e.g., '254/26/2123').
    """
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    invoice_date = Column(String(20), nullable=False)   # Stored as string "26/Feb/2026"

    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    customer_type = Column(String(50), default="")      # Override per invoice

    destination = Column(String(100), default="")
    currency = Column(String(10), default="USD")
    payment_method = Column(String(50), default="TT")
    shipping_method = Column(String(100), default="N/A")
    reference = Column(String(200), default="")

    freight = Column(Float, default=0.0)
    notes = Column(Text, default="(Any Applicable Tax should be born by the Customer)")
    delivery_note = Column(Text, default="")           # e.g. "Delivered in Nairobi"

    status = Column(String(20), default="draft")       # draft | sent | paid
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="invoices")
    line_items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")

    @property
    def goods_total(self):
        """Sum of all line item amounts."""
        return sum(item.amount for item in self.line_items)

    @property
    def invoice_total(self):
        """Goods total plus freight."""
        return self.goods_total + (self.freight or 0.0)


class InvoiceItem(Base):
    """
    Individual line item on an invoice.
    Description and price can be edited per-line (overrides catalog defaults).
    """
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)

    item_code = Column(String(100), nullable=False)     # Free text or catalog code
    description = Column(Text, nullable=False)          # Editable per line
    quantity = Column(Float, default=1.0)
    unit_price = Column(Float, default=0.0)

    # Amount is stored (quantity * unit_price) for display consistency
    @property
    def amount(self):
        """Computed line amount."""
        return self.quantity * self.unit_price

    invoice = relationship("Invoice", back_populates="line_items")


class Settings(Base):
    """
    Key-value store for application settings such as company info and bank details.
    A single row per key makes it easy to add new settings without schema changes.
    """
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, default="")

    # Key names used by the application:
    # company_name, company_address, company_license, company_tel, company_email
    # bank_ac_name, bank_ac_number, bank_iban, bank_name, bank_swift
    # logo_path
