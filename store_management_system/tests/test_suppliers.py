"""
Automated unit and integration tests for Supplier Management and Referential Integrity.
"""

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pytest
from database.storage_manager import StorageManager
from utils.validators import validate_supplier_data


def test_add_supplier_success(isolated_storage_env: StorageManager):
    """Tests adding a new valid supplier."""
    sm = isolated_storage_env
    new_supp = {
        "supplier_id": "SUP-999",
        "supplier_name": "Test International Logistics",
        "contact_number": "+1-555-0899",
        "email": "contact@testintl.com",
        "address": "900 Global Port Rd, Oakland, CA",
        "product_category": "Logistics & Freight",
    }
    success, msg = sm.add_supplier(new_supp)
    assert success is True

    supps = sm.get_suppliers()
    assert "SUP-999" in supps["supplier_id"].values
    saved = supps[supps["supplier_id"] == "SUP-999"].iloc[0]
    assert saved["supplier_name"] == "Test International Logistics"


def test_add_duplicate_supplier_rejected(isolated_storage_env: StorageManager):
    """Tests that duplicate supplier IDs are rejected."""
    sm = isolated_storage_env
    supps = sm.get_suppliers()
    existing_id = supps.iloc[0]["supplier_id"]

    dup = {
        "supplier_id": existing_id,
        "supplier_name": "Duplicate Supplier Co.",
        "contact_number": "+1-555-0111",
        "email": "dup@test.com",
        "address": "123 Dup St",
        "product_category": "General",
    }
    success, msg = sm.add_supplier(dup)
    assert success is False
    assert "already exists" in msg.lower()


def test_delete_supplier_blocked_when_products_linked(isolated_storage_env: StorageManager):
    """
    CRITICAL REFERENTIAL INTEGRITY TEST:
    Supplier with linked products must NOT be deleted.
    """
    sm = isolated_storage_env
    prods = sm.get_products()
    linked_supp_id = prods.iloc[0]["supplier_id"]

    success, msg = sm.delete_supplier(linked_supp_id)
    assert success is False
    assert "cannot delete supplier" in msg.lower()
    assert "linked" in msg.lower()

    # Verify supplier is still in dataset
    supps = sm.get_suppliers()
    assert linked_supp_id in supps["supplier_id"].values


def test_delete_supplier_allowed_when_unlinked(isolated_storage_env: StorageManager):
    """Supplier with NO linked products can be deleted safely."""
    sm = isolated_storage_env
    new_supp = {
        "supplier_id": "SUP-777",
        "supplier_name": "Unlinked Supplier LLC",
        "contact_number": "+1-555-0777",
        "email": "info@unlinked.com",
        "address": "777 Solitary Way, Reno, NV",
        "product_category": "Packaging",
    }
    sm.add_supplier(new_supp)
    assert "SUP-777" in sm.get_suppliers()["supplier_id"].values

    # Now delete
    success, msg = sm.delete_supplier("SUP-777")
    assert success is True
    assert "SUP-777" not in sm.get_suppliers()["supplier_id"].values


def test_supplier_validation_rules():
    """Unit tests for phone and email validation rules."""
    # Invalid email
    ok, msg, _ = validate_supplier_data("SUP-1", "Test", "+1-555-0123", "bad_email_format", "123 Way", "Pantry", [])
    assert ok is False
    assert "valid email" in msg.lower()

    # Invalid phone
    ok, msg, _ = validate_supplier_data("SUP-1", "Test", "12", "good@test.com", "123 Way", "Pantry", [])
    assert ok is False
    assert "valid phone" in msg.lower()

