"""
Automated unit and integration tests for Expiry Classification and Alerts.
"""

from datetime import date, timedelta
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pytest

from database.storage_manager import StorageManager
from utils.helpers import calculate_days_until, classify_expiry_status


def test_expiry_classification_tiers():
    """Unit tests for status classification thresholds."""
    assert classify_expiry_status(-5) == "EXPIRED"
    assert classify_expiry_status(0) == "EXPIRED"
    assert classify_expiry_status(1) == "EXPIRING_SOON_7"
    assert classify_expiry_status(7) == "EXPIRING_SOON_7"
    assert classify_expiry_status(8) == "EXPIRING_SOON_30"
    assert classify_expiry_status(30) == "EXPIRING_SOON_30"
    assert classify_expiry_status(31) == "SAFE"
    assert classify_expiry_status(365) == "SAFE"


def test_calculate_days_until():
    """Unit tests for date delta calculation."""
    ref = date(2026, 11, 4)
    assert calculate_days_until("2026-11-04", ref_date=ref) == 0
    assert calculate_days_until("2026-11-09", ref_date=ref) == 5
    assert calculate_days_until("2026-10-30", ref_date=ref) == -5


def test_expiry_alerts_dataset_populated(isolated_storage_env: StorageManager):
    """Verifies that expiry alerts are loaded and populated for products."""
    sm = isolated_storage_env
    alerts = sm.get_expiry_alerts()
    assert not alerts.empty
    assert "alert_id" in alerts.columns
    assert "alert_status" in alerts.columns

    # Verify presence of multiple statuses
    statuses = set(alerts["alert_status"].unique())
    assert "SAFE" in statuses


def test_update_alert_notification(isolated_storage_env: StorageManager):
    """Tests updating notification status from Pending to Sent."""
    sm = isolated_storage_env
    alerts = sm.get_expiry_alerts()
    target_alert = alerts.iloc[0]["alert_id"]

    success, msg = sm.update_alert_notification(target_alert, new_status="Sent")
    assert success is True

    reloaded = sm.get_expiry_alerts()
    row = reloaded[reloaded["alert_id"] == target_alert].iloc[0]
    assert row["notification_sent"] == "Sent"

