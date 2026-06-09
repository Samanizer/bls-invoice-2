"""
routers/reports.py - Reporting endpoints.
  GET /api/reports/summary       — overall totals and top customers/items
  GET /api/reports/customers     — per-customer invoice activity
  GET /api/reports/items         — per-item usage activity
  GET /api/settings              — get current app settings
  PUT /api/settings              — update app settings
  POST /api/settings/logo        — upload company logo
"""

import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
import models, schemas
from auth import get_current_user

router = APIRouter(tags=["reports & settings"])

LOGO_DIR = os.environ.get("LOGO_DIR", "./data/")


# ── Reports ───────────────────────────────────────────────────────────────────

@router.get("/api/reports/summary", response_model=schemas.ReportResponse)
def get_summary(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user)
):
    """Return a full activity report: per-customer and per-item breakdowns."""
    # Total invoices and revenue (goods total ignores freight for simplicity in reporting)
    all_invoices = db.query(models.Invoice).all()
    total_invoices = len(all_invoices)
    total_revenue = sum(inv.invoice_total for inv in all_invoices)

    customer_activity = _build_customer_activity(db)
    item_activity     = _build_item_activity(db)

    return schemas.ReportResponse(
        customer_activity=customer_activity,
        item_activity=item_activity,
        total_invoices=total_invoices,
        total_revenue=total_revenue,
    )


@router.get("/api/reports/customers", response_model=List[schemas.CustomerActivity])
def report_customers(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user)
):
    """Return invoice count and total amount per customer, sorted by amount descending."""
    return _build_customer_activity(db)


@router.get("/api/reports/items", response_model=List[schemas.ItemActivity])
def report_items(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user)
):
    """Return usage statistics per item code, sorted by total amount descending."""
    return _build_item_activity(db)


def _build_customer_activity(db: Session) -> List[schemas.CustomerActivity]:
    """Aggregate invoices by customer."""
    rows = (
        db.query(
            models.Invoice.customer_id,
            func.count(models.Invoice.id).label("invoice_count"),
        )
        .group_by(models.Invoice.customer_id)
        .all()
    )
    result = []
    for row in rows:
        customer = db.query(models.Customer).filter(models.Customer.id == row.customer_id).first()
        invoices = db.query(models.Invoice).filter(models.Invoice.customer_id == row.customer_id).all()
        total = sum(inv.invoice_total for inv in invoices)
        result.append(schemas.CustomerActivity(
            customer_id=row.customer_id,
            customer_name=customer.name if customer else "Unknown",
            invoice_count=row.invoice_count,
            total_amount=total,
        ))
    result.sort(key=lambda x: x.total_amount, reverse=True)
    return result


def _build_item_activity(db: Session) -> List[schemas.ItemActivity]:
    """Aggregate line item usage by item code."""
    rows = (
        db.query(
            models.InvoiceItem.item_code,
            func.count(models.InvoiceItem.id).label("times_used"),
            func.sum(models.InvoiceItem.quantity).label("total_qty"),
        )
        .group_by(models.InvoiceItem.item_code)
        .all()
    )
    result = []
    for row in rows:
        # Find the latest description for this code
        latest = (
            db.query(models.InvoiceItem)
            .filter(models.InvoiceItem.item_code == row.item_code)
            .order_by(models.InvoiceItem.id.desc())
            .first()
        )
        # Sum amounts manually
        all_lines = db.query(models.InvoiceItem).filter(models.InvoiceItem.item_code == row.item_code).all()
        total_amt = sum(li.amount for li in all_lines)
        result.append(schemas.ItemActivity(
            item_code=row.item_code,
            description=latest.description if latest else "",
            times_used=row.times_used,
            total_quantity=row.total_qty or 0,
            total_amount=total_amt,
        ))
    result.sort(key=lambda x: x.total_amount, reverse=True)
    return result


# ── Settings ──────────────────────────────────────────────────────────────────

@router.get("/api/settings", response_model=schemas.SettingsResponse)
def get_settings(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user)
):
    """Return all application settings as a flat key→value dict."""
    rows = db.query(models.Settings).all()
    return {"settings": {row.key: row.value for row in rows}}


@router.put("/api/settings", response_model=schemas.SettingsResponse)
def update_settings(
    payload: schemas.SettingsUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user)
):
    """
    Upsert settings key-value pairs.
    Creates missing keys, updates existing ones.
    """
    for key, value in payload.settings.items():
        row = db.query(models.Settings).filter(models.Settings.key == key).first()
        if row:
            row.value = value
        else:
            db.add(models.Settings(key=key, value=value))
    db.commit()
    rows = db.query(models.Settings).all()
    return {"settings": {row.key: row.value for row in rows}}


@router.post("/api/settings/logo")
def upload_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user)
):
    """
    Upload a company logo image.
    Saves to /data/logo.<ext> and updates the logo_path setting.
    """
    os.makedirs(LOGO_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1].lower() or ".png"
    logo_path = os.path.join(LOGO_DIR, f"logo{ext}")
    with open(logo_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Store relative path in settings
    row = db.query(models.Settings).filter(models.Settings.key == "logo_path").first()
    if row:
        row.value = logo_path
    else:
        db.add(models.Settings(key="logo_path", value=logo_path))
    db.commit()
    return {"message": "Logo uploaded", "logo_path": logo_path}
