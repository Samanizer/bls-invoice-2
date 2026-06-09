"""
routers/customers.py - Customer CRUD endpoints.
  GET    /api/customers         — list all active customers
  POST   /api/customers         — create new customer
  GET    /api/customers/{id}    — get single customer
  PUT    /api/customers/{id}    — update customer
  DELETE /api/customers/{id}    — soft-delete customer (sets is_active=False)
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
import models, schemas
from auth import get_current_user

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("", response_model=List[schemas.CustomerResponse])
def list_customers(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user)
):
    """Return all active customers, ordered by name."""
    return (
        db.query(models.Customer)
        .filter(models.Customer.is_active == True)
        .order_by(models.Customer.name)
        .all()
    )


@router.post("", response_model=schemas.CustomerResponse, status_code=201)
def create_customer(
    payload: schemas.CustomerCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user)
):
    """Create and return a new customer record."""
    customer = models.Customer(**payload.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/{customer_id}", response_model=schemas.CustomerResponse)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user)
):
    """Return a single customer by ID."""
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.put("/{customer_id}", response_model=schemas.CustomerResponse)
def update_customer(
    customer_id: int,
    payload: schemas.CustomerUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user)
):
    """Update an existing customer record."""
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    for field, value in payload.model_dump().items():
        setattr(customer, field, value)
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}")
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user)
):
    """Soft-delete a customer (marks is_active=False, preserves invoice history)."""
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    customer.is_active = False
    db.commit()
    return {"message": "Customer deleted"}
