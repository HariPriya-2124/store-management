"""
Automated unit tests for SMS Dispatch Service and Persistent Logging.
Tests phone normalization, gateway dispatching, and storage audit logging.
"""

import sys
from pathlib import Path
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from utils.sms_service import normalize_phone_number, dispatch_sms
from database.storage_manager import StorageManager


@pytest.fixture(scope="module")
def storage():
    """Provides a StorageManager instance."""
    return StorageManager(auto_init=True)


def test_normalize_phone_number():
    """Tests phone cleaning, country code prepending, and validation."""
    # 10 digit Indian number without country code
    ok, num, err = normalize_phone_number("9876543210")
    assert ok is True
    assert num == "+919876543210"

    # With spaces, hyphens, and country code
    ok, num, err = normalize_phone_number("+91 98765-43210")
    assert ok is True
    assert num == "+919876543210"

    # US number
    ok, num, err = normalize_phone_number("+1 555-0199222")
    assert ok is True
    assert num == "+15550199222"

    # Invalid empty or letters
    ok, num, err = normalize_phone_number("")
    assert ok is False

    ok, num, err = normalize_phone_number("abcdefg")
    assert ok is False


def test_simulated_sms_dispatch():
    """Tests simulated gateway SMS dispatch."""
    res = dispatch_sms(
        phone_raw="9876543210",
        message="Urgent restock needed for item PRD-0001",
        recipient_name="Farm Supplier",
        message_type="Restock Notice",
        gateway_mode="simulated",
    )
    assert res["success"] is True
    assert res["status"] == "Delivered"
    assert res["phone"] == "+919876543210"
    assert "delivery_id" in res
    assert res["gateway"] == "Simulated Telecom Gateway"


def test_auto_fallback_sms_dispatch():
    """Tests auto gateway SMS dispatch (with graceful fallback if offline)."""
    res = dispatch_sms(
        phone_raw="+91 9123456780",
        message="Order is ready for pickup",
        recipient_name="Customer Jane",
        message_type="Order Ready",
        gateway_mode="auto",
    )
    assert res["success"] is True
    assert res["status"] == "Delivered"
    assert res["phone"] == "+919123456780"


def test_sms_storage_persistence(storage):
    """Tests saving and retrieving dispatched SMS records in persistent CSV storage."""
    sms_payload = {
        "sms_id": "SMS-TEST-001",
        "timestamp": "2026-11-13 10:55:00",
        "recipient_phone": "+919876543210",
        "recipient_name": "Test Supplier",
        "message_type": "Restock Notice",
        "message_body": "Test message body content",
        "gateway": "Simulated Gateway",
        "status": "Delivered",
        "delivery_id": "TEL-999888",
    }
    ok, msg = storage.record_sms_log(sms_payload)
    assert ok is True

    df_logs = storage.get_sms_logs()
    assert not df_logs.empty
    assert "SMS-TEST-001" in df_logs["sms_id"].values
    matched = df_logs[df_logs["sms_id"] == "SMS-TEST-001"].iloc[0]
    assert matched["recipient_phone"] == "+919876543210"
    assert matched["status"] == "Delivered"
