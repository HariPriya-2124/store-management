"""
Automated unit and integration tests for Product Management.
"""

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pytest
from database.storage_manager import StorageManager
from utils.validators import validate_product_data


def test_add_product_success(isolated_storage_env: StorageManager):
    """Verifies that a valid product can be added, and an initial stock movement is logged."""
    sm = isolated_storage_env
    new_prod = {
        "product_id": "PRD-9999",
        "product_name": "Premium Test Coffee Beans 1lb",
        "category": "Beverages",
        "supplier_id": "SUP-001",
        "purchase_price": "8.50",
        "selling_price": "16.00",
        "stock_quantity": "40",
        "minimum_stock": "10",
        "expiry_date": "2027-01-01",
    }
    success, msg = sm.add_product(new_prod)
    assert success is True

    # Check product is in dataset
    prods = sm.get_products()
    assert "PRD-9999" in prods["product_id"].values
    saved = prods[prods["product_id"] == "PRD-9999"].iloc[0]
    assert saved["product_name"] == "Premium Test Coffee Beans 1lb"
    assert saved["stock_quantity"] == "40"

    # Check INITIAL_STOCK movement was created
    movs = sm.get_stock_movements()
    prod_movs = movs[movs["product_id"] == "PRD-9999"]
    assert not prod_movs.empty
    assert prod_movs.iloc[0]["movement_type"] == "INITIAL_STOCK"
    assert prod_movs.iloc[0]["quantity_change"] == "40"


def test_add_duplicate_product_rejected(isolated_storage_env: StorageManager):
    """Ensures duplicate product IDs are rejected."""
    sm = isolated_storage_env
    prods = sm.get_products()
    existing_id = prods.iloc[0]["product_id"]

    dup_prod = {
        "product_id": existing_id,
        "product_name": "Duplicate Item",
        "category": "Beverages",
        "supplier_id": "SUP-001",
        "purchase_price": "5.00",
        "selling_price": "10.00",
        "stock_quantity": "10",
        "minimum_stock": "5",
        "expiry_date": "2027-01-01",
    }
    success, msg = sm.add_product(dup_prod)
    assert success is False
    assert "already exists" in msg.lower()


def test_add_product_invalid_supplier_rejected(isolated_storage_env: StorageManager):
    """Ensures referential integrity: foreign key supplier_id must exist."""
    sm = isolated_storage_env
    invalid_prod = {
        "product_id": "PRD-8888",
        "product_name": "Ghost Supplier Product",
        "category": "Pantry",
        "supplier_id": "SUP-999",  # Non-existent
        "purchase_price": "5.00",
        "selling_price": "10.00",
        "stock_quantity": "10",
        "minimum_stock": "5",
        "expiry_date": "2027-01-01",
    }
    success, msg = sm.add_product(invalid_prod)
    assert success is False
    assert "does not exist" in msg.lower()


def test_update_product_success(isolated_storage_env: StorageManager):
    """Tests updating an existing product's price and stock quantity."""
    sm = isolated_storage_env
    prods = sm.get_products()
    target_id = prods.iloc[0]["product_id"]

    updated = {
        "product_name": "Updated Item Name",
        "selling_price": "29.99",
        "stock_quantity": "88",
    }
    success, msg = sm.update_product(target_id, updated)
    assert success is True

    reloaded = sm.get_products()
    row = reloaded[reloaded["product_id"] == target_id].iloc[0]
    assert row["product_name"] == "Updated Item Name"
    assert row["selling_price"] == "29.99"
    assert row["stock_quantity"] == "88"


def test_delete_product_success(isolated_storage_env: StorageManager):
    """Tests product deletion and corresponding removal from expiry alerts."""
    sm = isolated_storage_env
    prods = sm.get_products()
    target_id = prods.iloc[0]["product_id"]

    success, msg = sm.delete_product(target_id)
    assert success is True

    prods_after = sm.get_products()
    assert target_id not in prods_after["product_id"].values

    alerts = sm.get_expiry_alerts()
    assert target_id not in alerts["product_id"].values


def test_product_input_validation():
    """Unit tests for product validation logic."""
    # Negative purchase price
    ok, msg, _ = validate_product_data("PRD-1", "A", "B", "SUP-1", "-5", "10", "1", "1", "2027-01-01", [])
    assert ok is False
    assert "greater than" in msg.lower()

    # Selling price below purchase price
    ok, msg, _ = validate_product_data("PRD-1", "A", "B", "SUP-1", "15", "10", "1", "1", "2027-01-01", [])
    assert ok is False
    assert "cannot be less than" in msg.lower()

    # Negative stock
    ok, msg, _ = validate_product_data("PRD-1", "A", "B", "SUP-1", "5", "10", "-3", "1", "2027-01-01", [])
    assert ok is False
    assert "integer >=" in msg.lower()

    # Invalid date format
    ok, msg, _ = validate_product_data("PRD-1", "A", "B", "SUP-1", "5", "10", "5", "1", "invalid-date", [])
    assert ok is False
    assert "yyyy-mm-dd" in msg.lower()

