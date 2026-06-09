"""
seed.py - Default data seed for the BLS Invoice application.
Seeds company info and bank details from the Bluelight sample invoice
if no settings rows exist yet. Safe to call on every startup.
"""

from sqlalchemy.orm import Session
import models

# Default settings matching the Bluelight sample invoice
DEFAULT_SETTINGS = {
    "company_name":      "BLUELIGHT FZCO",
    "company_address_1": "P.O. Box 377266",
    "company_address_2": "Dubai, UAE",
    "company_license":   "006-0003198-050918",
    "company_tel":       "+971 56 734 7794",
    "company_email":     "info@bluelightsystems.net",
    "bank_ac_name":      "Bluelight",
    "bank_ac_number":    "11275363920002 (USD Account)",
    "bank_iban":         "AE060030011275363920002",
    "bank_name":         "Abu Dhabi Commercial Bank, Bank Street Branch, Dubai, UAE",
    "bank_swift":        "ADCBAEAA",
    "logo_path":         "",
}


def seed_default_settings(db: Session):
    """
    Insert default settings only if the settings table is empty.
    This preserves any changes the user has made.
    """
    if db.query(models.Settings).count() == 0:
        for key, value in DEFAULT_SETTINGS.items():
            db.add(models.Settings(key=key, value=value))
        db.commit()
        print("Default settings seeded.")
