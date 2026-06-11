"""
pdf_generator.py - PDF invoice generator for the BLS Invoice application.

The design follows the Invoice_Sample.pdf "pre-printed form" aesthetic: the
labels read like a typewriter form's printed captions (bold Courier) and the
customer / item / financial data reads like it was typed into the form (plain
Courier). The top half (letterhead, invoice bar, customer block, details grid)
matches the reference sample coordinate-for-coordinate; the lower half has been
refined for a more professional look:

  - Items table now carries a Unit Price column (Item | Description | Quantity |
    Unit Price | Amount) with a softly shaded header band and a smaller row font.
  - Bank Details and the Goods/Freight/Invoice-Total summary sit side-by-side in
    matching boxes; long bank lines wrap so they never overflow their box.
  - Totals values are baseline-aligned with their labels (the sample's values
    floated off their captions); the Invoice Total row is highlighted.
  - The page number sits in a proper centred footer.

Fonts: the sample's Arial/Calibri (sans) and Courier New (monospace) map to the
ReportLab base-14 Helvetica and Courier families.
"""

import os
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas

PAGE_W, PAGE_H = A4          # 595.27 × 841.89 pt

# ── Logo ──────────────────────────────────────────────────────────────────────
# Default company logo shown top-left of the invoice. To change the logo, either
# replace this file or point DEFAULT_LOGO_PATH at another image. A logo uploaded
# through the app (Settings → logo_path) still takes precedence over this default.
DEFAULT_LOGO_PATH = os.path.join(os.path.dirname(__file__), "assets", "logo.png")

# Placement of the logo (points, origin bottom-left). The image is scaled to fit
# inside this box while preserving its aspect ratio.
LOGO_X, LOGO_Y = 42, 772
LOGO_W, LOGO_H = 130, 47

# ── Fonts ─────────────────────────────────────────────────────────────────────
SANS    = "Helvetica"
SANS_B  = "Helvetica-Bold"
MONO    = "Courier"          # the "typed" data
MONO_B  = "Courier-Bold"     # the "pre-printed" form captions

# ── Colours ───────────────────────────────────────────────────────────────────
GRAY_BAR   = colors.Color(0.847, 0.847, 0.847)   # invoice number bar   (#D8D8D8)
HEADER_BG  = colors.Color(0.93, 0.93, 0.93)      # table header shading  (#EDEDED)
LIGHT_BLUE = colors.Color(0.706, 0.78, 0.906)    # invoice-total highlight (#B4C7E7)
HAIRLINE   = colors.Color(0.45, 0.45, 0.45)      # thin internal rules
BLACK      = colors.black


# ── Primitive drawing helpers ─────────────────────────────────────────────────

def _text(c, x, y, txt, font=MONO, size=9, color=BLACK):
    """Draw a left-aligned string at (x, y)."""
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawString(x, y, str(txt))


def _text_right(c, x, y, txt, font=MONO, size=9, color=BLACK):
    """Draw a right-aligned string ending at x."""
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawRightString(x, y, str(txt))


def _line(c, x1, y1, x2, y2, width=0.75, color=BLACK):
    """Stroke a line."""
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.line(x1, y1, x2, y2)


def _rect(c, x, y, w, h, fill=None, stroke=BLACK, width=0.75):
    """Draw a rectangle: optional fill, optional stroke."""
    if fill is not None:
        c.setFillColor(fill)
        c.rect(x, y, w, h, fill=1, stroke=0)
    if stroke is not None:
        c.setStrokeColor(stroke)
        c.setLineWidth(width)
        c.rect(x, y, w, h, fill=0, stroke=1)


def _wrap(c, text, font, size, max_w):
    """Greedy word-wrap; returns a list of lines that each fit within max_w."""
    lines, cur = [], ""
    for word in str(text).split():
        trial = (cur + " " + word).strip()
        if c.stringWidth(trial, font, size) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ── Section renderers ─────────────────────────────────────────────────────────

def _draw_header(c, settings, logo_path):
    """Company logo (top-left) and company details block (right, left-aligned)."""
    # Prefer a logo uploaded via the app; otherwise fall back to the bundled one.
    if not (logo_path and os.path.exists(logo_path)):
        logo_path = DEFAULT_LOGO_PATH
    if os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, LOGO_X, LOGO_Y, width=LOGO_W, height=LOGO_H,
                        preserveAspectRatio=True, anchor="nw", mask="auto")
        except Exception:
            pass  # silently skip an unreadable image

    bx = 397.57
    lines = [
        (settings.get("company_name", "BLUELIGHT FZCO"),        SANS_B, 819.7),
        (settings.get("company_address_1", "P.O. Box 377266"),  SANS,   810.4),
        (settings.get("company_address_2", "Dubai, UAE"),       SANS,   801.2),
        (f"License No: {settings.get('company_license', '')}",  SANS,   791.9),
        (f"Tel: {settings.get('company_tel', '')}",             SANS,   782.7),
        (settings.get("company_email", ""),                     SANS,   773.4),
    ]
    for txt, font, y in lines:
        if str(txt).strip():
            _text(c, bx, y, txt, font, 7)


def _draw_invoice_bar(c, invoice_number, invoice_date):
    """Grey bar with the pre-printed INVOICE / No: / Date: captions."""
    _rect(c, 31.5, 739.85, 536.25, 24.75, fill=GRAY_BAR, stroke=BLACK, width=0.75)

    y = 747.5
    _text(c, 38.7,  y, "INVOICE", MONO_B, 9)
    _text(c, 254.8, y, "No:",   MONO_B, 9)
    _text(c, 281.8, y, invoice_number, MONO, 9)
    _text(c, 434.8, y, "Date:", MONO_B, 9)
    _text(c, 467.2, y, invoice_date, MONO, 9)


def _draw_customer(c, customer, customer_type):
    """Customer label, name (uppercased), address and the type tag on the right."""
    _text(c, 72, 707.7, "Customer:", MONO_B, 9)

    y = 693.8
    for ln in (customer.name or "").upper().split("\n"):
        _text(c, 108, y, ln, MONO_B, 10)   # typed (bold Courier)
        y -= 14
    for ln in (customer.address or "").split("\n"):
        _text(c, 108, y, ln, MONO, 9)      # typed (Courier)
        y -= 13

    if customer_type:
        _text(c, 396.1, 693.8, customer_type, MONO, 9)


def _draw_details_grid(c, invoice):
    """Three-column details grid with the boxed Payment cell on the right."""
    col1, col2, col3 = 72, 252.1, 432.1

    _rect(c, 417.75, 595.8, 141.0, 54.75, fill=None, stroke=BLACK, width=0.75)

    _text(c, col1, 628.0, "Destination:",      MONO_B, 9)
    _text(c, col2, 628.0, "Invoice Currency:", MONO_B, 9)
    _text(c, col3, 628.0, "Payment:",          MONO_B, 9)
    _text(c, col1, 616.3, invoice.destination or "",      MONO, 9)
    _text(c, col2, 616.3, invoice.currency or "USD",      MONO, 9)
    _text(c, col3, 616.3, invoice.payment_method or "TT", MONO, 9)

    _text(c, col1, 604.6, "Shipping Method:", MONO_B, 9)
    _text(c, col2, 604.6, "Ref / Proforma:",  MONO_B, 9)
    _text(c, col1, 592.9, invoice.shipping_method or "N/A", MONO, 9)
    _text(c, col2, 592.9, invoice.reference or "",          MONO, 9)


# Items table geometry (right edges for the numeric columns)
_ITEM_X  = 72
_DESC_X  = 140
_QTY_RX  = 372
_PRICE_RX = 466
_AMT_RX  = 553
_TBL_L, _TBL_R = 42, 558.75


def _draw_items_table(c, line_items):
    """Items table: shaded header band, captions, and the flowing typed rows."""
    top_rule, bot_rule = 580.03, 543.14

    # Shaded header band between the two rules
    _rect(c, _TBL_L, bot_rule, _TBL_R - _TBL_L, top_rule - bot_rule,
          fill=HEADER_BG, stroke=None)
    _line(c, _TBL_L, top_rule, _TBL_R, top_rule, width=0.75)
    _line(c, _TBL_L, bot_rule, _TBL_R, bot_rule, width=0.75)

    # Column captions (pre-printed form headings)
    _text(c, _ITEM_X,   558.5, "Item",        MONO_B, 8)
    _text(c, _DESC_X,   558.5, "Description", MONO_B, 8)
    _text_right(c, _QTY_RX,   558.5, "Quantity",   MONO_B, 8)
    _text_right(c, _PRICE_RX, 558.5, "Unit Price", MONO_B, 8)
    _text_right(c, _AMT_RX,   558.5, "Amount",     MONO_B, 8)
    _text_right(c, _AMT_RX,   548.1, "(USD)",      MONO_B, 8)

    # Typed data rows — smaller font, uniform line height
    size, line_h = 7, 9.6
    y = 516.8
    for item in line_items:
        desc_lines = (item.description or "").split("\n")
        unit_price = getattr(item, "unit_price", None)
        if unit_price is None and item.quantity:
            unit_price = item.amount / item.quantity
        _text(c, _ITEM_X, y, item.item_code or "", MONO, size)
        _text(c, _DESC_X, y, desc_lines[0] if desc_lines else "", MONO, size)
        _text_right(c, _QTY_RX,   y, f"{item.quantity:g}",        MONO, size)
        _text_right(c, _PRICE_RX, y, f"{(unit_price or 0):,.2f}", MONO, size)
        _text_right(c, _AMT_RX,   y, f"{item.amount:,.2f}",       MONO, size)
        y -= line_h
        for extra in desc_lines[1:]:
            _text(c, _DESC_X, y, extra, MONO, size)
            y -= line_h


def _draw_notes(c, notes):
    """Disclaimer / notes, in the band just above the financial summary."""
    if notes:
        y = 224
        for ln in _wrap(c, notes, MONO, 8, _TBL_R - _ITEM_X):
            _text(c, _ITEM_X, y, ln, MONO, 8)
            y -= 11


# Bottom summary band — Bank box (left) and Totals box (right), side by side
_BAND_TOP, _BAND_BOT = 206, 78
_BANK_X, _BANK_W = 72, 258
_TOT_X,  _TOT_W  = 345, 214


def _draw_bank_box(c, settings):
    """Bank Details box (lower-left); long values wrap to stay inside the box."""
    h = _BAND_TOP - _BAND_BOT
    _rect(c, _BANK_X, _BAND_BOT, _BANK_W, h, fill=colors.white, stroke=BLACK, width=0.75)

    x = _BANK_X + 8
    max_w = _BANK_W - 16
    _text(c, x, _BAND_TOP - 17, "Bank Details:", SANS_B, 9)

    fields = [
        ("A/C Name:",   settings.get("bank_ac_name", ""),   False),
        ("A/C Number:", settings.get("bank_ac_number", ""), False),
        ("IBAN:",       settings.get("bank_iban", ""),      True),   # value bold
        ("Bank:",       settings.get("bank_name", ""),      False),
        ("Swift:",      settings.get("bank_swift", ""),     False),
    ]
    y = _BAND_TOP - 32
    size, line_h = 8.5, 11.5
    for label, value, value_bold in fields:
        vfont = SANS_B if value_bold else SANS
        _text(c, x, y, label, SANS_B, size)
        label_w = c.stringWidth(label + " ", SANS_B, size)
        first = True
        for ln in _wrap(c, value, vfont, size, max_w - label_w):
            _text(c, x + (label_w if first else 0), y, ln, vfont, size)
            y -= line_h
            first = False
        if first:                     # empty value: still advance one line
            y -= line_h


def _draw_totals(c, invoice):
    """Goods Total / Freight / Invoice Total box (lower-right), baseline-aligned."""
    top, bot = _BAND_TOP, _BAND_BOT
    r1, r2 = 165, 125                 # internal row dividers
    val_rx = _TOT_X + _TOT_W - 8      # values right-align here
    lab_x  = _TOT_X + 8

    # Invoice-total highlight (bottom row), drawn behind borders
    _rect(c, _TOT_X, bot, _TOT_W, r2 - bot, fill=LIGHT_BLUE, stroke=None)

    # Box and internal rules
    _rect(c, _TOT_X, bot, _TOT_W, top - bot, fill=None, stroke=BLACK, width=0.75)
    _line(c, _TOT_X, r1, _TOT_X + _TOT_W, r1, width=0.6, color=HAIRLINE)
    _line(c, _TOT_X, r2, _TOT_X + _TOT_W, r2, width=0.6, color=HAIRLINE)

    # Goods Total
    _text(c, lab_x, 182, "Goods Total", MONO_B, 9)
    _text_right(c, val_rx, 182, f"{invoice.goods_total:,.2f}", MONO, 9)

    # Freight
    _text(c, lab_x, 142, "Freight", MONO_B, 9)
    _text_right(c, val_rx, 142, f"{(invoice.freight or 0):,.2f}", MONO, 9)

    # Invoice Total (caption + currency, optional delivery note, bold value)
    cap_y = 104 if invoice.delivery_note else 99
    _text(c, lab_x, cap_y, "Invoice Total", MONO_B, 11)
    cur_x = lab_x + c.stringWidth("Invoice Total ", MONO_B, 11)
    _text(c, cur_x, cap_y, invoice.currency or "USD", MONO_B, 11)
    if invoice.delivery_note:
        _text(c, lab_x, cap_y - 13, f"({invoice.delivery_note})", MONO, 8)
    _text_right(c, val_rx, 99, f"{invoice.invoice_total:,.2f}", MONO_B, 11)


def _draw_footer(c, page, total_pages):
    """Centred page-number footer with a thin separator rule."""
    _line(c, _ITEM_X, 60, _TBL_R, 60, width=0.5, color=HAIRLINE)
    label, value = "Page: ", f"{page}/{total_pages}"
    total_w = (c.stringWidth(label, MONO_B, 8) + c.stringWidth(value, MONO, 8))
    x = (PAGE_W - total_w) / 2
    _text(c, x, 46, label, MONO_B, 8)
    _text(c, x + c.stringWidth(label, MONO_B, 8), 46, value, MONO, 8)


# ── Public API ────────────────────────────────────────────────────────────────

def generate_invoice_pdf(invoice, settings: dict, logo_path: str = None) -> bytes:
    """
    Generate a PDF byte string for the given invoice object.

    Args:
        invoice   : Invoice ORM object with .customer and .line_items populated
        settings  : Dict of setting key→value from the Settings table
        logo_path : Filesystem path to the company logo image (optional)

    Returns:
        bytes — the raw PDF file content
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    _draw_header(c, settings, logo_path)
    _draw_invoice_bar(c, invoice.invoice_number, invoice.invoice_date)
    _draw_customer(c, invoice.customer, invoice.customer_type)
    _draw_details_grid(c, invoice)
    _draw_items_table(c, invoice.line_items)
    _draw_notes(c, invoice.notes)
    _draw_bank_box(c, settings)
    _draw_totals(c, invoice)
    _draw_footer(c, 1, 1)

    c.save()
    return buffer.getvalue()
