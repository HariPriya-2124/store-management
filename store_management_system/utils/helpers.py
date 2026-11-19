"""
General helper functions for data manipulation, formatting, and ID generation.
"""

import re
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, Optional
import pandas as pd
from config import (
    CURRENCY_SYMBOL,
    EXPIRY_CAUTION_DAYS,
    EXPIRY_CRITICAL_DAYS,
    EXPIRY_WARNING_DAYS,
)

def format_currency(amount: any, symbol: str = CURRENCY_SYMBOL) -> str:
    """Formats a float or int into a currency string (e.g., ₹1,249.50)."""
    try:
        val = float(amount)
        return f"{symbol}{val:,.2f}"
    except (ValueError, TypeError):
        return f"{symbol}0.00"

def format_quantity(qty: any) -> str:
    """Formats an integer quantity with commas (e.g., 1,500)."""
    try:
        val = int(qty)
        return f"{val:,}"
    except (ValueError, TypeError):
        return "0"

def safe_float(val: any, default: float = 0.0) -> float:
    """Safely converts a value to float without throwing."""
    try:
        if pd.isna(val):
            return default
        return float(val)
    except (ValueError, TypeError):
        return default

def safe_int(val: any, default: int = 0) -> int:
    """Safely converts a value to integer without throwing."""
    try:
        if pd.isna(val):
            return default
        return int(float(val))
    except (ValueError, TypeError):
        return default

def generate_next_id(prefix: str, existing_ids: Iterable[str], pad_length: int = 4) -> str:
    """
    Generates the next sequential ID given a prefix (e.g. 'PRD-', 'SUP-', 'TXN-', 'MOV-', 'ALT-').
    Extracts the highest existing integer suffix and increments by 1.
    """
    highest = 0
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$", re.IGNORECASE)
    for id_val in existing_ids:
        if not id_val or not isinstance(id_val, str):
            continue
        match = pattern.match(id_val.strip())
        if match:
            try:
                num = int(match.group(1))
                if num > highest:
                    highest = num
            except ValueError:
                pass

    next_num = highest + 1
    return f"{prefix}{str(next_num).zfill(pad_length)}"

def calculate_days_until(target_date_str: str, ref_date: Optional[date] = None) -> int:
    """
    Calculates number of calendar days from ref_date (default: today) until target_date.
    Negative return indicates already expired.
    """
    if ref_date is None:
        ref_date = date.today()
    try:
        if isinstance(target_date_str, (datetime, date)):
            t_date = target_date_str.date() if isinstance(target_date_str, datetime) else target_date_str
        else:
            t_date = datetime.strptime(str(target_date_str).strip(), "%Y-%m-%d").date()
        return (t_date - ref_date).days
    except Exception:
        return 999999

def classify_expiry_status(days_remaining: int) -> str:
    """
    Classifies a product into an expiry status string based on days remaining:
    - 'EXPIRED'
    - 'EXPIRING_SOON_7'
    - 'EXPIRING_SOON_30'
    - 'SAFE'
    """
    if days_remaining <= EXPIRY_CRITICAL_DAYS:
        return "EXPIRED"
    elif days_remaining <= EXPIRY_WARNING_DAYS:
        return "EXPIRING_SOON_7"
    elif days_remaining <= EXPIRY_CAUTION_DAYS:
        return "EXPIRING_SOON_30"
    else:
        return "SAFE"

def export_dataframe_to_csv(df: pd.DataFrame, file_path: Path) -> tuple[bool, str]:
    """Safely exports a pandas DataFrame to a target CSV file."""
    try:
        target = Path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(target, index=False, encoding="utf-8")
        return True, f"Successfully exported {len(df)} records to {target.name}"
    except Exception as e:
        return False, f"Failed to export data: {str(e)}"

