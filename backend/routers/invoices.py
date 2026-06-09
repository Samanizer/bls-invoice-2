"""
routers/invoices.py - Invoice CRUD + PDF generation endpoints.
  GET    /api/invoices              — list all invoices (summary)
  POST   /api/invoices              — create invoice with line items
  GET    /api/invoices/{id}         — get full invoice detail
  PUT    /api/invoices/{id}         — update invoice and replace line items
  DELETE /api/invoices/{id}         — delete invoice
  GET    /api/invoices/{id}/pdf     — download PDF matching the sample format
  POST   /api/invoices/next-number  — suggest next sequential invoice number
"""

import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from database import get_db
import models, schemas
from auth import get_current_user
from pdf_generator import generate_invoice_pdf

router = APIRouter(prefix="/api/invoices", tags=["invoices"])


def _get_settings_dict(db: Session) -> dict:
    """Load all Settings rows into a simple key→value dict."""
    rows = db.query(models.Settings).all()
    return {row.key: row.value for row in rows}


@router.get("", response_model=List[schemas.InvoiceSummary])
def list_invoices(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user)
):
    """Return all invoices ordered by newest first (summary, no line items)."""
    invoices = (
        db.query(models.Invoice)
        .order_by(models.Invoice.created_at.desc())
        .all()
    )
    result = []
    for inv in invoices:
        result.append(schemas.InvoiceSummary(
            id=inv.id,
            invoice_number=inv.invoice_number,
            invoice_date=inv.invoice_date,
            customer_id=inv.customer_id,
            currency=inv.currency,
            invoice_total=inv.invoice_total,
            status=inv.status,
            customer=inv.customer,
        ))
    return result


@router.post("", response_model=schemas.InvoiceResponse, status_code=201)
def create_invoice(
    payload: schemas.InvoiceCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user)
):
    """
    Create a new invoice with its line items.
    Invoice number must be unique.
    """
    if db.query(models.Invoice).filter(models.Invoice.invoice_number == payload.invoice_number).first():
        raise HTTPException(status_code=400, detail="Invoice number already exists")

    # Verify customer exists
    customer = db.query(models.Customer).filter(models.Customer.id == payload.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Create invoice header
    inv_data = payload.model_dump(exclude={"line_items"})
    invoice = models.Invoice(**inv_data)
    db.add(invoice)
    db.flush()   # get invoice.id before adding children

    # Add line items
    for li in payload.line_items:
        line = models.InvoiceItem(invoice_id=invoice.id, **li.model_dump())
        db.add(line)

    db.commit()
    db.refresh(invoice)
    return _invoice_to_response(invoice)


@router.get("/next-number")
def next_invoice_number(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user)
):
    """
    Suggest the next invoice number.
    Format: {last_seq + 1}/{YY}/{series}  where series is 4-digit running count.
    Returns a simple suggestion string that the user can edit.
    """
    from datetime import datetime
    year_short = datetime.utcnow().strftime("%y")
    count = db.query(models.Invoice).count() + 1
    return {"invoice_number": f"{count}/{year_short}/{count:04d}"}


@router.get("/{invoice_id}", response_model=schemas.InvoiceResponse)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user)
):
    """Return full invoice detail including line items and customer."""
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return _invoice_to_response(invoice)


@router.put("/{invoice_id}", response_model=schemas.InvoiceResponse)
def update_invoice(
    invoice_id: int,
    payload: schemas.InvoiceUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user)
):
    """
    Replace an invoice's header fields and line items.
    All existing line items are deleted and re-created from the payload.
    """
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Check number uniqueness (allow if unchanged)
    if payload.invoice_number != invoice.invoice_number:
        if db.query(models.Invoice).filter(models.Invoice.invoice_number == payload.invoice_number).first():
            raise HTTPException(status_code=400, detail="Invoice number already exists")

    # Update header fields
    for field, value in payload.model_dump(exclude={"line_items"}).items():
        setattr(invoice, field, value)

    # Replace line items
    db.query(models.InvoiceItem).filter(models.InvoiceItem.invoice_id == invoice_id).delete()
    for li in payload.line_items:
        line = models.InvoiceItem(invoice_id=invoice_id, **li.model_dump())
        db.add(line)

    db.commit()
    db.refresh(invoice)
    return _invoice_to_response(invoice)


@router.delete("/{invoice_id}")
def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user)
):
    """Permanently delete an invoice and its line items."""
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    db.delete(invoice)
    db.commit()
    return {"message": "Invoice deleted"}


@router.get("/{invoice_id}/pdf")
def download_pdf(
    invoice_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user)
):
    """
    Generate and return a PDF for the invoice.
    The PDF layout exactly matches Invoice_Sample.pdf.
    """
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    settings = _get_settings_dict(db)

    # Resolve logo path
    logo_path = settings.get("logo_path", "")
    if logo_path and not os.path.isabs(logo_path):
        logo_path = os.path.join(os.path.dirname(__file__), "..", logo_path)

    pdf_bytes = generate_invoice_pdf(invoice, settings, logo_path or None)

    filename = f"invoice_{invoice.invoice_number.replace('/', '-')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ── Internal helper ───────────────────────────────────────────────────────────

def _invoice_to_response(invoice: models.Invoice) -> schemas.InvoiceResponse:
    """Map Invoice ORM object to the full response schema."""
    line_items = [
        schemas.InvoiceItemResponse(
            id=li.id,
            item_code=li.item_code,
            description=li.description,
            quantity=li.quantity,
            unit_price=li.unit_price,
            amount=li.amount,
        )
        for li in invoice.line_items
    ]
    return schemas.InvoiceResponse(
        id=invoice.id,
        invoice_number=invoice.invoice_number,
        invoice_date=invoice.invoice_date,
        customer_id=invoice.customer_id,
        customer_type=invoice.customer_type,
        destination=invoice.destination,
        currency=invoice.currency,
        payment_method=invoice.payment_method,
        shipping_method=invoice.shipping_method,
        reference=invoice.reference,
        freight=invoice.freight,
        notes=invoice.notes,
        delivery_note=invoice.delivery_note,
        status=invoice.status,
        goods_total=invoice.goods_total,
        invoice_total=invoice.invoice_total,
        line_items=line_items,
        customer=invoice.customer,
    )
