"""
Automated unit and integration tests for Inventory Movements and Reconciliations.
"""

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pytest
from database.storage_manager import StorageManager


def test_stock_in_receiving(isolated_storage_env: StorageManager):
    """Tests restock delivery increasing stock and recording movement."""
    sm = isolated_storage_env
    prods = sm.get_products()
    pid = prods.iloc[0]["product_id"]
    initial_stock = int(prods.iloc[0]["stock_quantity"])

    add_qty = 25
    success, msg = sm.record_stock_movement(
        product_id=pid,
        movement_type="PURCHASE_RECEIPT",
        quantity_change=add_qty,
        notes="PO-8822 Restock delivery"
    )
    assert success is True

    prods_after = sm.get_products()
    new_stock = int(prods_after[prods_after["product_id"] == pid].iloc[0]["stock_quantity"])
    assert new_stock == initial_stock + add_qty

    movs = sm.get_stock_movements()
    latest_mov = movs[movs["product_id"] == pid].iloc[-1]
    assert latest_mov["movement_type"] == "PURCHASE_RECEIPT"
    assert int(latest_mov["quantity_change"]) == add_qty


def test_stock_out_damage_write_off(isolated_storage_env: StorageManager):
    """Tests writing off damaged inventory."""
    sm = isolated_storage_env
    prods = sm.get_products()
    pid = prods.iloc[0]["product_id"]
    initial_stock = int(prods.iloc[0]["stock_quantity"])

    deduct_qty = 4
    success, msg = sm.record_stock_movement(
        product_id=pid,
        movement_type="DAMAGED_WRITE_OFF",
        quantity_change=-deduct_qty,
        notes="Broken seal carton write-off"
    )
    assert success is True

    prods_after = sm.get_products()
    new_stock = int(prods_after[prods_after["product_id"] == pid].iloc[0]["stock_quantity"])
    assert new_stock == initial_stock - deduct_qty


def test_prevent_negative_stock_balance(isolated_storage_env: StorageManager):
    """Tests that any movement causing negative inventory is blocked."""
    sm = isolated_storage_env
    prods = sm.get_products()
    pid = prods.iloc[0]["product_id"]
    initial_stock = int(prods.iloc[0]["stock_quantity"])

    excessive_deduction = -(initial_stock + 100)
    success, msg = sm.record_stock_movement(
        product_id=pid,
        movement_type="DAMAGED_WRITE_OFF",
        quantity_change=excessive_deduction
    )
    assert success is False
    assert "negative stock balance" in msg.lower()


def test_manual_stock_reconciliation(isolated_storage_env: StorageManager):
    """Tests physical audit count setting stock and logging variance."""
    sm = isolated_storage_env
    prods = sm.get_products()
    pid = prods.iloc[0]["product_id"]
    initial_stock = int(prods.iloc[0]["stock_quantity"])

    physical_count = initial_stock + 7
    success, msg = sm.manual_stock_reconciliation(
        product_id=pid,
        physical_count=physical_count,
        reason="Physical shelf inventory audit count"
    )
    assert success is True

    prods_after = sm.get_products()
    new_stock = int(prods_after[prods_after["product_id"] == pid].iloc[0]["stock_quantity"])
    assert new_stock == physical_count

    # Check movement logged as MANUAL_ADJUSTMENT with variance +7
    movs = sm.get_stock_movements()
    latest_mov = movs[movs["product_id"] == pid].iloc[-1]
    assert latest_mov["movement_type"] == "MANUAL_ADJUSTMENT"
    assert int(latest_mov["quantity_change"]) == 7

