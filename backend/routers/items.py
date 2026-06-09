"""
routers/items.py - Item catalog CRUD endpoints.
  GET    /api/items         — list all active items
  POST   /api/items         — create new item
  GET    /api/items/{id}    — get single item
  PUT    /api/items/{id}    — update item
  DELETE /api/items/{id}    — soft-delete item
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
import models, schemas
from auth import get_current_user

router = APIRouter(prefix="/api/items", tags=["items"])


@router.get("", response_model=List[schemas.ItemResponse])
def list_items(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user)
):
    """Return all active catalog items, ordered by code."""
    return (
        db.query(models.Item)
        .filter(models.Item.is_active == True)
        .order_by(models.Item.code)
        .all()
    )


@router.post("", response_model=schemas.ItemResponse, status_code=201)
def create_item(
    payload: schemas.ItemCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user)
):
    """Create and return a new catalog item. Item code must be unique."""
    if db.query(models.Item).filter(models.Item.code == payload.code).first():
        raise HTTPException(status_code=400, detail="Item code already exists")
    item = models.Item(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=schemas.ItemResponse)
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user)
):
    """Return a single catalog item by ID."""
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.put("/{item_id}", response_model=schemas.ItemResponse)
def update_item(
    item_id: int,
    payload: schemas.ItemUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user)
):
    """Update a catalog item. Changing a code checks for uniqueness."""
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    # If code is changing, check it's not already used
    if payload.code != item.code:
        existing = db.query(models.Item).filter(models.Item.code == payload.code).first()
        if existing:
            raise HTTPException(status_code=400, detail="Item code already exists")
    for field, value in payload.model_dump().items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}")
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user)
):
    """Soft-delete an item (marks is_active=False)."""
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item.is_active = False
    db.commit()
    return {"message": "Item deleted"}
