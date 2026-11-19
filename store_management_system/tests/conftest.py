"""
Pytest configuration and isolated fixtures for Store Management System.
Ensures tests run in isolated temporary directories without modifying production datasets.
"""

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pytest
from database.storage_manager import StorageManager


@pytest.fixture
def isolated_storage_env(tmp_path):
    """
    Directs all data, backups, and logs to a temporary directory for each test run.
    """
    test_data_dir = tmp_path / "data"
    test_backups_dir = tmp_path / "backups"
    test_logs_dir = tmp_path / "logs"

    test_data_dir.mkdir(parents=True, exist_ok=True)
    test_backups_dir.mkdir(parents=True, exist_ok=True)
    test_logs_dir.mkdir(parents=True, exist_ok=True)

    # Initialize isolated storage manager with temp paths
    sm = StorageManager(data_dir=test_data_dir, backup_dir=test_backups_dir, auto_init=True)
    return sm
