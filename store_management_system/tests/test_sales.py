"""
Automated unit and integration tests for Sales Transactions and POS Workflow.
"""

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pytest
from database.storage_manager import StorageManager
from utils.validators import validate_sale_request


def test_sales_calculation_and_execution(isolated_storage_env: StorageManager):
    """
    Tests successful sale:
    - Verifies product stock deduction
    - Verifies sales ledger record
    - Verifies stock movement ledger record
    """
    sm = isolated_storage_env
    prods = sm.get_products()
    target_prod = prods.iloc[0]
    pid = target_prod["product_id"]
    initial_stock = int(target_prod["stock_quantity"])
    unit_price = float(target_prod["selling_price"])

    sale_qty = 3
    success, msg, receipt = sm.record_sale(
        product_id=pid,
        quantity=sale_qty,
        unit_price=unit_price,
        sale_date="2026-11-04"
    )
    assert success is True
    assert receipt is not None
    assert receipt["quantity"] == sale_qty
    assert receipt["total_amount"] == round(sale_qty * unit_price, 2)
    assert receipt["remaining_stock"] == initial_stock - sale_qty

    # Check Product Stock was deducted
    prods_after = sm.get_products()
    updated_stock = int(prods_after[prods_after["product_id"] == pid].iloc[0]["stock_quantity"])
    assert updated_stock == initial_stock - sale_qty

    # Check Sales dataset
    sales_df = sm.get_sales()
    tx_row = sales_df[sales_df["transaction_id"] == receipt["transaction_id"]]
    assert not tx_row.empty
    assert tx_row.iloc[0]["product_id"] == pid
    assert int(tx_row.iloc[0]["quantity"]) == sale_qty

    # Check Stock Movements dataset
    mov_df = sm.get_stock_movements()
    prod_movs = mov_df[(mov_df["product_id"] == pid) & (mov_df["movement_type"] == "SALE")]
    assert not prod_movs.empty
    latest_mov = prod_movs.iloc[-1]
    assert int(latest_mov["quantity_change"]) == -sale_qty
    assert receipt["transaction_id"] in latest_mov["notes"]


def test_sale_insufficient_stock_rejected(isolated_storage_env: StorageManager):
    """Verifies that sales exceeding current stock are rejected and do not modify data."""
    sm = isolated_storage_env
    prods = sm.get_products()
    target = prods.iloc[0]
    pid = target["product_id"]
    current_stock = int(target["stock_quantity"])
    unit_price = float(target["selling_price"])

    excess_qty = current_stock + 50
    success, msg, receipt = sm.record_sale(
        product_id=pid,
        quantity=excess_qty,
        unit_price=unit_price
    )
    assert success is False
    assert receipt is None
    assert "insufficient stock" in msg.lower()

    # Verify stock remained untouched
    prods_after = sm.get_products()
    unchanged_stock = int(prods_after[prods_after["product_id"] == pid].iloc[0]["stock_quantity"])
    assert unchanged_stock == current_stock


def test_sale_zero_or_negative_quantity_rejected(isolated_storage_env: StorageManager):
    """Verifies that zero or negative sale quantities are rejected."""
    sm = isolated_storage_env
    prods = sm.get_products()
    pid = prods.iloc[0]["product_id"]

    success, msg, _ = sm.record_sale(product_id=pid, quantity=0, unit_price=10.0)
    assert success is False
    assert "at least 1" in msg.lower()

    success, msg, _ = sm.record_sale(product_id=pid, quantity=-5, unit_price=10.0)
    assert success is False


def test_sale_request_validation():
    """Unit test for validate_sale_request helper."""
    ok, msg, qty, tot = validate_sale_request("PRD-001", 5, current_stock=10, unit_price=12.50)
    assert ok is True
    assert qty == 5
    assert tot == 62.50

    ok, msg, _, _ = validate_sale_request("PRD-001", 15, current_stock=10, unit_price=12.50)
    assert ok is False
    assert "insufficient" in msg.lower()

