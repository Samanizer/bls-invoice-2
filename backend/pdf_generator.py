"""
pdf_generator.py - PDF invoice generator for the BLS Invoice application.
Uses ReportLab to produce a PDF that exactly matches the Invoice_Sample.pdf layout:
  - Company header (logo left, company info right)
  - Invoice number/date bar
  - Customer block with type tag
  - Details grid (Destination, Currency, Payment, Shipping, Reference)
  - Line items table
  - Notes text
  - Bank details box (bottom-left) and totals section (bottom-right)
  - Page number
"""

import os
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_LEFT

PAGE_W, PAGE_H = A4          # 595.27 × 841.89 pt
L_MARGIN = 40                # left margin
R_MARGIN = 40                # right margin
BODY_W = PAGE_W - L_MARGIN - R_MARGIN   # usable width

# ── Font helpers ──────────────────────────────────────────────────────────────

FONT_NORMAL = "Helvetica"
FONT_BOLD   = "Helvetica-Bold"
FONT_MONO   = "Courier"
FONT_MONO_B = "Courier-Bold"

# ── Color palette ─────────────────────────────────────────────────────────────

GRAY_BAR   = colors.HexColor("#E8E8E8")   # Invoice number bar background
DARK_BOX   = colors.HexColor("#1e3a8a")   # Invoice total highlight — deep Bluelight blue
LIGHT_BOX  = colors.HexColor("#F5F5F5")   # Payment box background
BORDER_CLR = colors.HexColor("#555555")   # Table/box borders


# ── Utility drawing helpers ───────────────────────────────────────────────────

def _line(c, x1, y1, x2, y2, width=0.5, color=BORDER_CLR):
    """Draw a horizontal or vertical line."""
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.line(x1, y1, x2, y2)


def _rect(c, x, y, w, h, fill_color=None, stroke_color=BORDER_CLR, line_width=0.5):
    """Draw a rectangle, optionally filled."""
    c.setLineWidth(line_width)
    c.setStrokeColor(stroke_color)
    if fill_color:
        c.setFillColor(fill_color)
        c.rect(x, y, w, h, fill=1)
        c.setFillColor(colors.black)
    else:
        c.rect(x, y, w, h, fill=0)


def _text(c, x, y, txt, font=FONT_NORMAL, size=9, color=colors.black):
    """Draw a single text string at (x, y)."""
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawString(x, y, str(txt))


def _text_right(c, x, y, txt, font=FONT_NORMAL, size=9, color=colors.black):
    """Draw text right-aligned to x."""
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawRightString(x, y, str(txt))


def _wrap_text(c, x, y, txt, font, size, max_width):
    """
    Draw text that may wrap onto multiple lines.
    Returns the y position after the last line drawn.
    Each line descends by (size + 2) points.
    """
    c.setFont(font, size)
    c.setFillColor(colors.black)
    words = txt.split()
    line = ""
    line_h = size + 2
    for word in words:
        test = f"{line} {word}".strip()
        if c.stringWidth(test, font, size) <= max_width:
            line = test
        else:
            c.drawString(x, y, line)
            y -= line_h
            line = word
    if line:
        c.drawString(x, y, line)
        y -= line_h
    return y


# ── Section renderers ─────────────────────────────────────────────────────────

def _draw_header(c, settings, logo_path):
    """
    Draw the company logo (top-left) and company details (top-right).
    Returns the y-coordinate after the header.
    """
    top_y = PAGE_H - L_MARGIN

    # Logo area — draw image if available, otherwise text placeholder
    logo_box_w = 160
    logo_box_h = 70
    if logo_path and os.path.exists(logo_path):
        try:
            c.drawImage(
                logo_path,
                L_MARGIN, top_y - logo_box_h,
                width=logo_box_w, height=logo_box_h,
                preserveAspectRatio=True, anchor="c"
            )
        except Exception:
            pass  # silently skip if image can't be loaded

    # Company info block — right-aligned to page right margin
    right_x = PAGE_W - R_MARGIN
    cy = top_y - 8

    company_lines = [
        (settings.get("company_name", "BLUELIGHT FZCO"), FONT_BOLD, 11),
        (settings.get("company_address_1", "P.O. Box 377266"), FONT_NORMAL, 9),
        (settings.get("company_address_2", "Dubai, UAE"), FONT_NORMAL, 9),
        (f"License No: {settings.get('company_license', '')}", FONT_NORMAL, 8),
        (f"Tel: {settings.get('company_tel', '')}", FONT_NORMAL, 8),
        (settings.get("company_email", ""), FONT_NORMAL, 8),
    ]
    for txt, font, size in company_lines:
        if txt.strip():
            _text_right(c, right_x, cy, txt, font, size)
            cy -= (size + 3)

    return top_y - logo_box_h - 8   # y below header


def _draw_invoice_bar(c, invoice_number, invoice_date, y):
    """
    Draw the gray 'INVOICE | No: xxx | Date: xxx' bar.
    'INVOICE', 'No:' and 'Date:' labels are bold; values are normal weight.
    Returns y below the bar.
    """
    bar_h = 24
    _rect(c, L_MARGIN, y - bar_h, BODY_W, bar_h, fill_color=GRAY_BAR, line_width=0.3)

    bar_mid_y = y - bar_h + 7   # vertical centre of text in bar

    # "INVOICE" label — bold, far left
    _text(c, L_MARGIN + 6, bar_mid_y, "INVOICE", FONT_BOLD, 10)

    # "No:" bold + invoice number normal — centred in the bar
    mid_x = PAGE_W / 2
    _text(c, mid_x - 60, bar_mid_y, "No:", FONT_BOLD, 9)
    _text(c, mid_x - 40, bar_mid_y, invoice_number, FONT_NORMAL, 9)

    # "Date:" bold + date value normal — right-aligned as one combined unit.
    # Compute total width so the phrase sits flush to the right margin.
    label_part = "Date:  "
    total_date_w = (c.stringWidth(label_part, FONT_BOLD, 9) +
                    c.stringWidth(invoice_date, FONT_NORMAL, 9))
    date_x = PAGE_W - R_MARGIN - 6 - total_date_w
    _text(c, date_x, bar_mid_y, "Date:", FONT_BOLD, 9)
    _text(c, date_x + c.stringWidth(label_part, FONT_BOLD, 9),
          bar_mid_y, invoice_date, FONT_NORMAL, 9)

    return y - bar_h - 10


def _draw_customer(c, customer, customer_type, y):
    """
    Draw the customer block. Returns y below the section.
    """
    _text(c, L_MARGIN, y, "Customer:", FONT_BOLD, 9)
    y -= 14

    name_lines = (customer.name or "").upper().split("\n")
    for ln in name_lines:
        _text(c, L_MARGIN + 20, y, ln, FONT_BOLD, 11)
        y -= 14

    addr_lines = (customer.address or "").split("\n")
    for ln in addr_lines:
        _text(c, L_MARGIN + 20, y, ln, FONT_NORMAL, 9)
        y -= 12

    # Customer type label on the right (e.g. "EXPORT")
    if customer_type:
        _text(c, PAGE_W / 2, y + len(addr_lines) * 12 + 14, customer_type, FONT_NORMAL, 9)

    return y - 6


def _draw_details_grid(c, invoice, y):
    """
    Draw the 3-column details grid:
      Left  — Destination / Shipping Method
      Middle — Invoice Currency / Ref/Proforma
      Right  — Payment (boxed)
    Returns y below the section.
    """
    col1_x = L_MARGIN
    col2_x = L_MARGIN + BODY_W * 0.35
    col3_x = L_MARGIN + BODY_W * 0.68

    row_h = 13
    box_top = y
    box_bot = y - 70

    # Payment box (right column) ← draw first so it appears behind text
    pay_box_w = PAGE_W - R_MARGIN - col3_x
    _rect(c, col3_x - 4, box_bot, pay_box_w + 4, box_top - box_bot,
          stroke_color=BORDER_CLR, line_width=0.6)

    # Left column
    _text(c, col1_x, y - row_h, "Destination:", FONT_BOLD, 9)
    _text(c, col1_x, y - row_h * 2, invoice.destination or "", FONT_MONO, 9)
    _text(c, col1_x, y - row_h * 3.5, "Shipping Method:", FONT_BOLD, 9)
    _text(c, col1_x, y - row_h * 4.5, invoice.shipping_method or "N/A", FONT_MONO, 9)

    # Middle column
    _text(c, col2_x, y - row_h, "Invoice Currency:", FONT_BOLD, 9)
    _text(c, col2_x, y - row_h * 2, invoice.currency or "USD", FONT_MONO, 9)
    _text(c, col2_x, y - row_h * 3.5, "Ref / Proforma:", FONT_BOLD, 9)
    _text(c, col2_x, y - row_h * 4.5, invoice.reference or "", FONT_MONO, 9)

    # Right column (inside box)
    _text(c, col3_x, y - row_h, "Payment:", FONT_BOLD, 9)
    _text(c, col3_x, y - row_h * 2, invoice.payment_method or "TT", FONT_MONO, 9)

    return box_bot - 12


def _draw_items_table(c, line_items, y):
    """
    Draw the items table (header + rows).
    Columns: Item | Description | Quantity | Amount (USD)
    Quantity and Amount columns are both right-aligned so narrow values like "1"
    sit directly under their column headers.
    Returns y below the last row.
    """
    col_item_x    = L_MARGIN               # Item code — left-aligned
    col_desc_x    = L_MARGIN + 90          # Description — left-aligned
    col_qty_rx    = PAGE_W - R_MARGIN - 95 # Quantity — RIGHT-align reference point
    col_amt_x     = PAGE_W - R_MARGIN      # Amount — RIGHT-align reference point

    row_h     = 13
    font_size = 9
    line_h    = font_size + 2              # proper baseline-to-baseline distance

    # ── Separator line above headers ────────────────────────────────────────
    _line(c, L_MARGIN, y, PAGE_W - R_MARGIN, y, width=0.8)
    y -= (font_size + 3)   # drop to header baseline

    # ── Column headers (row 1) ───────────────────────────────────────────────
    header_y = y
    _text(c, col_item_x, header_y, "Item",        FONT_BOLD, font_size)
    _text(c, col_desc_x, header_y, "Description", FONT_BOLD, font_size)
    _text_right(c, col_qty_rx, header_y, "Quantity",    FONT_BOLD, font_size)
    _text_right(c, col_amt_x,  header_y, "Amount",      FONT_BOLD, font_size)

    # ── Column headers (row 2) — only Amount has a second line "(USD)" ───────
    header_y2 = header_y - line_h
    _text_right(c, col_amt_x, header_y2, "(USD)", FONT_BOLD, font_size)

    # ── Separator line below headers (below both header rows) ────────────────
    y = header_y2 - (font_size + 3)
    _line(c, L_MARGIN, y, PAGE_W - R_MARGIN, y, width=0.8)
    y -= row_h + 2

    # ── Data rows ────────────────────────────────────────────────────────────
    for item in line_items:
        desc_lines = (item.description or "").split("\n")
        _text(c, col_item_x, y, item.item_code or "", FONT_MONO, font_size)
        _text(c, col_desc_x, y, desc_lines[0],         FONT_MONO, font_size)
        _text_right(c, col_qty_rx, y, f"{item.quantity:g}",    FONT_MONO, font_size)
        _text_right(c, col_amt_x,  y, f"{item.amount:,.2f}",   FONT_MONO, font_size)
        y -= row_h
        # Additional description lines
        for extra_line in desc_lines[1:]:
            _text(c, col_desc_x, y, extra_line, FONT_MONO, font_size)
            y -= row_h

    return y - 6


def _draw_notes(c, notes, y):
    """Draw the notes/disclaimer text. Returns y below it."""
    if notes:
        _text(c, L_MARGIN + 20, y, notes, FONT_MONO, 8)
        y -= 14
    return y


def _draw_footer(c, invoice, settings, totals_y):
    """
    Draw the combined footer:
      Left half  — Bank Details box
      Right half — Goods Total / Freight / Invoice Total
    totals_y is the TOP of the footer area.
    """
    footer_h = 120
    footer_top    = totals_y
    footer_bottom = totals_y - footer_h

    # ── Bank Details box ──────────────────────────────────────────────────
    bank_box_w = BODY_W * 0.55
    _rect(c, L_MARGIN, footer_bottom, bank_box_w, footer_h,
          stroke_color=BORDER_CLR, line_width=0.6)

    bx = L_MARGIN + 6
    by = footer_top - 14
    _text(c, bx, by, "Bank Details:", FONT_BOLD, 9)
    by -= 12
    bank_fields = [
        f"A/C Name: {settings.get('bank_ac_name', '')}",
        f"A/C Number: {settings.get('bank_ac_number', '')}",
        f"IBAN: {settings.get('bank_iban', '')}",
        f"Bank: {settings.get('bank_name', '')}",
        f"Swift: {settings.get('bank_swift', '')}",
    ]
    for i, field in enumerate(bank_fields):
        # Bold IBAN line
        font = FONT_BOLD if "IBAN:" in field else FONT_NORMAL
        _text(c, bx, by, field, font, 8)
        by -= 11

    # ── Totals section (right side) ───────────────────────────────────────
    tot_x      = L_MARGIN + bank_box_w + 4
    tot_right  = PAGE_W - R_MARGIN
    tot_w      = tot_right - tot_x

    row_h_tot = footer_h / 3

    # Box borders for each row
    for i in range(3):
        row_y = footer_top - (i + 1) * row_h_tot
        _rect(c, tot_x, row_y, tot_w, row_h_tot,
              stroke_color=BORDER_CLR, line_width=0.5)

    # Row 1 — Goods Total
    row1_mid = footer_top - row_h_tot / 2 - 4
    _text(c, tot_x + 6, row1_mid, "Goods Total", FONT_BOLD, 9)
    _text_right(c, tot_right - 6, row1_mid,
                f"{invoice.goods_total:,.2f}", FONT_MONO, 9)

    # Row 2 — Freight
    row2_mid = footer_top - row_h_tot - row_h_tot / 2 - 4
    _text(c, tot_x + 6, row2_mid, "Freight", FONT_BOLD, 9)
    _text_right(c, tot_right - 6, row2_mid,
                f"{(invoice.freight or 0):,.2f}", FONT_MONO, 9)

    # Row 3 — Invoice Total (dark background highlight)
    row3_top_y = footer_bottom
    _rect(c, tot_x, row3_top_y, tot_w, row_h_tot,
          fill_color=DARK_BOX, stroke_color=DARK_BOX)
    row3_mid   = footer_bottom + row_h_tot / 2 - 4

    label_lines = [f"Invoice Total {invoice.currency or 'USD'}"]
    if invoice.delivery_note:
        label_lines.append(f"({invoice.delivery_note})")

    label_y = row3_mid + 4
    for ln in label_lines:
        _text(c, tot_x + 6, label_y, ln, FONT_BOLD, 9, color=colors.white)
        label_y -= 11

    _text_right(c, tot_right - 6, row3_mid + 4,
                f"{invoice.invoice_total:,.2f}", FONT_MONO_B, 11,
                color=colors.white)


def _draw_page_number(c, page, total_pages):
    """Draw 'Page: X/Y' at the bottom right."""
    _text_right(
        c, PAGE_W - R_MARGIN,
        L_MARGIN - 14,
        f"Page: {page}/{total_pages}",
        FONT_NORMAL, 8
    )


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

    # ── Draw header ──────────────────────────────────────────────────────
    y = _draw_header(c, settings, logo_path)
    y -= 6

    # ── Invoice bar ──────────────────────────────────────────────────────
    y = _draw_invoice_bar(c, invoice.invoice_number, invoice.invoice_date, y)

    # ── Customer block ───────────────────────────────────────────────────
    y -= 8
    y = _draw_customer(c, invoice.customer, invoice.customer_type, y)

    # ── Details grid ─────────────────────────────────────────────────────
    y -= 6
    y = _draw_details_grid(c, invoice, y)

    # ── Items table ──────────────────────────────────────────────────────
    y = _draw_items_table(c, invoice.line_items, y)

    # ── Notes ────────────────────────────────────────────────────────────
    y = _draw_notes(c, invoice.notes, y)

    # ── Footer — always pinned to the bottom ─────────────────────────────
    footer_top = 40 + 120 + 10   # bottom margin + footer height + padding
    _draw_footer(c, invoice, settings, footer_top)

    # ── Page number ──────────────────────────────────────────────────────
    _draw_page_number(c, 1, 1)

    c.save()
    return buffer.getvalue()
