"""
Input validation utilities for Store Management System.
Ensures strict data integrity, preventing invalid or malicious records.
"""

import re
from datetime import datetime
from typing import Any, Optional, Tuple

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_REGEX = re.compile(r"^\+?[0-9\s\-\(\)]{7,20}$")
DATE_FORMAT = "%Y-%m-%d"

def validate_non_empty(value: Any, field_name: str) -> Tuple[bool, str]:
    """Validates that a string/field is not empty or whitespace only."""
    if value is None:
        return False, f"{field_name} cannot be empty."
    if isinstance(value, str) and not value.strip():
        return False, f"{field_name} cannot be empty or blank."
    return True, ""

def validate_positive_float(value: Any, field_name: str, allow_zero: bool = False) -> Tuple[bool, str, float]:
    """Validates that a value can be converted to a positive float."""
    try:
        val = float(value)
        if allow_zero:
            if val < 0:
                return False, f"{field_name} must be greater than or equal to 0.0.", 0.0
        else:
            if val <= 0:
                return False, f"{field_name} must be strictly greater than 0.0.", 0.0
        return True, "", val
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid numeric number.", 0.0

def validate_integer(value: Any, field_name: str, min_val: Optional[int] = 0) -> Tuple[bool, str, int]:
    """Validates that a value is an integer with an optional minimum constraint."""
    try:
        val = int(value)
        if min_val is not None and val < min_val:
            return False, f"{field_name} must be an integer >= {min_val}.", 0
        return True, "", val
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid whole integer.", 0

def validate_date(date_str: str, field_name: str = "Date") -> Tuple[bool, str, Optional[datetime]]:
    """Validates that a date string matches the YYYY-MM-DD format and is logically valid."""
    if not date_str or not str(date_str).strip():
        return False, f"{field_name} cannot be blank.", None
    clean_str = str(date_str).strip()
    try:
        dt = datetime.strptime(clean_str, DATE_FORMAT)
        return True, "", dt
    except ValueError:
        return False, f"{field_name} must be in YYYY-MM-DD format (e.g., 2026-12-31).", None

def validate_email(email_str: str) -> Tuple[bool, str]:
    """Validates standard email address format."""
    if not email_str or not str(email_str).strip():
        return False, "Email address cannot be empty."
    clean_email = str(email_str).strip()
    if not EMAIL_REGEX.match(clean_email):
        return False, f"'{clean_email}' is not a valid email address format."
    return True, ""

def validate_phone(phone_str: str) -> Tuple[bool, str]:
    """Validates standard telephone number format."""
    if not phone_str or not str(phone_str).strip():
        return False, "Contact number cannot be empty."
    clean_phone = str(phone_str).strip()
    if not PHONE_REGEX.match(clean_phone):
        return False, f"'{clean_phone}' is not a valid phone number."
    return True, ""

def validate_product_data(
    product_id: str,
    product_name: str,
    category: str,
    supplier_id: str,
    purchase_price: Any,
    selling_price: Any,
    stock_quantity: Any,
    minimum_stock: Any,
    expiry_date: str,
    existing_product_ids: list,
    is_update: bool = False
) -> Tuple[bool, str, dict]:
    """
    Validates complete product input schema.
    Returns (is_valid, error_message, cleaned_dict).
    """
    # 1. Product ID
    ok, msg = validate_non_empty(product_id, "Product ID")
    if not ok:
        return False, msg, {}
    clean_pid = str(product_id).strip().upper()
    if not is_update and clean_pid in existing_product_ids:
        return False, f"Product ID '{clean_pid}' already exists. Please choose a unique ID.", {}

    # 2. Product Name
    ok, msg = validate_non_empty(product_name, "Product Name")
    if not ok:
        return False, msg, {}
    clean_name = str(product_name).strip()

    # 3. Category
    ok, msg = validate_non_empty(category, "Category")
    if not ok:
        return False, msg, {}
    clean_category = str(category).strip()

    # 4. Supplier ID
    ok, msg = validate_non_empty(supplier_id, "Supplier ID")
    if not ok:
        return False, msg, {}
    clean_supplier = str(supplier_id).strip().upper()

    # 5. Prices
    ok, msg, p_price = validate_positive_float(purchase_price, "Purchase Price", allow_zero=False)
    if not ok:
        return False, msg, {}

    ok, msg, s_price = validate_positive_float(selling_price, "Selling Price", allow_zero=False)
    if not ok:
        return False, msg, {}

    if s_price < p_price:
        # Selling below cost warning / rejection
        return False, f"Selling price (₹{s_price:.2f}) cannot be less than purchase price (₹{p_price:.2f}).", {}

    # 6. Quantities
    ok, msg, stock_qty = validate_integer(stock_quantity, "Stock Quantity", min_val=0)
    if not ok:
        return False, msg, {}

    ok, msg, min_stock = validate_integer(minimum_stock, "Minimum Stock Threshold", min_val=0)
    if not ok:
        return False, msg, {}

    # 7. Expiry Date
    ok, msg, dt_expiry = validate_date(expiry_date, "Expiry Date")
    if not ok:
        return False, msg, {}

    cleaned = {
        "product_id": clean_pid,
        "product_name": clean_name,
        "category": clean_category,
        "supplier_id": clean_supplier,
        "purchase_price": round(p_price, 2),
        "selling_price": round(s_price, 2),
        "stock_quantity": stock_qty,
        "minimum_stock": min_stock,
        "expiry_date": dt_expiry.strftime(DATE_FORMAT),
    }
    return True, "", cleaned

def validate_supplier_data(
    supplier_id: str,
    supplier_name: str,
    contact_number: str,
    email: str,
    address: str,
    product_category: str,
    existing_supplier_ids: list,
    is_update: bool = False
) -> Tuple[bool, str, dict]:
    """Validates complete supplier input schema."""
    ok, msg = validate_non_empty(supplier_id, "Supplier ID")
    if not ok:
        return False, msg, {}
    clean_sid = str(supplier_id).strip().upper()
    if not is_update and clean_sid in existing_supplier_ids:
        return False, f"Supplier ID '{clean_sid}' already exists. Please choose a unique ID.", {}

    ok, msg = validate_non_empty(supplier_name, "Supplier Name")
    if not ok:
        return False, msg, {}

    ok, msg = validate_phone(contact_number)
    if not ok:
        return False, msg, {}

    ok, msg = validate_email(email)
    if not ok:
        return False, msg, {}

    ok, msg = validate_non_empty(address, "Address")
    if not ok:
        return False, msg, {}

    ok, msg = validate_non_empty(product_category, "Product Category")
    if not ok:
        return False, msg, {}

    cleaned = {
        "supplier_id": clean_sid,
        "supplier_name": str(supplier_name).strip(),
        "contact_number": str(contact_number).strip(),
        "email": str(email).strip().lower(),
        "address": str(address).strip(),
        "product_category": str(product_category).strip(),
    }
    return True, "", cleaned

def validate_sale_request(
    product_id: str,
    quantity: Any,
    current_stock: int,
    unit_price: float
) -> Tuple[bool, str, int, float]:
    """
    Validates a sale transaction request.
    Ensures quantity is positive and available stock is sufficient.
    """
    ok, msg = validate_non_empty(product_id, "Product Selection")
    if not ok:
        return False, msg, 0, 0.0

    ok, msg, qty = validate_integer(quantity, "Sale Quantity", min_val=1)
    if not ok:
        return False, msg, 0, 0.0

    if qty > current_stock:
        return False, f"Insufficient stock! Requested: {qty}, Available: {current_stock}.", 0, 0.0

    if unit_price <= 0:
        return False, "Unit price must be strictly positive.", 0, 0.0

    total_amount = round(qty * unit_price, 2)
    return True, "", qty, total_amount

