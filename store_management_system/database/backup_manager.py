"""
Backup Manager module for Store Management System.
Handles automated and manual backups, backup integrity checks, and safe restoration.
"""

import os
import shutil
import zipfile
from datetime import datetime
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from typing import Dict, List, Optional, Tuple

from config import (
    BACKUPS_DIR,
    DATA_DIR,
    EXPIRY_ALERTS_FILE,
    PRODUCTS_FILE,
    SALES_FILE,
    STOCK_MOVEMENTS_FILE,
    SUPPLIERS_FILE,
)
from utils.logger import get_logger

logger = get_logger("BackupManager")

CORE_DATA_FILES = [
    PRODUCTS_FILE,
    SUPPLIERS_FILE,
    SALES_FILE,
    STOCK_MOVEMENTS_FILE,
    EXPIRY_ALERTS_FILE,
]


class BackupManager:
    """Manages creation, listing, verification, and restoration of database backups."""

    def __init__(self, backup_dir: Optional[Path] = None, data_dir: Optional[Path] = None):
        self.backup_dir = backup_dir or BACKUPS_DIR
        self.data_dir = data_dir or DATA_DIR
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, note: str = "manual") -> Tuple[bool, str, Optional[Path]]:
        """
        Creates a compressed .zip backup archive containing all 5 datasets.
        Returns (success, message, backup_file_path).
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sanitized_note = "".join(c for c in note if c.isalnum() or c in ("_", "-"))[:20]
            backup_filename = f"backup_{timestamp}_{sanitized_note}.zip"
            backup_path = self.backup_dir / backup_filename

            # Ensure all data files exist or create empty ones
            with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for file_path in CORE_DATA_FILES:
                    if file_path.exists():
                        zip_file.write(file_path, arcname=file_path.name)
                    else:
                        logger.warning(f"File {file_path.name} not found during backup.")

            size_kb = backup_path.stat().st_size / 1024
            msg = f"Backup created successfully: {backup_filename} ({size_kb:.1f} KB)"
            logger.info(msg)
            return True, msg, backup_path
        except Exception as e:
            err_msg = f"Failed to create backup: {str(e)}"
            logger.error(err_msg)
            return False, err_msg, None

    def list_backups(self) -> List[Dict[str, any]]:
        """
        Lists all available backup zip archives ordered by most recent first.
        """
        backups = []
        try:
            for p in sorted(self.backup_dir.glob("backup_*.zip"), key=os.path.getmtime, reverse=True):
                stat = p.stat()
                dt = datetime.fromtimestamp(stat.st_mtime)
                size_kb = stat.st_size / 1024
                backups.append({
                    "filename": p.name,
                    "path": p,
                    "timestamp": dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "size_kb": f"{size_kb:.1f} KB",
                    "file_count": self._count_files_in_zip(p),
                })
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
        return backups

    def _count_files_in_zip(self, zip_path: Path) -> int:
        """Counts the number of files inside a zip archive."""
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                return len(zf.namelist())
        except Exception:
            return 0

    def restore_backup(self, backup_filename_or_path: str) -> Tuple[bool, str]:
        """
        Safely restores datasets from a selected backup archive.
        Automatically creates a safety snapshot of current datasets before restoring.
        """
        try:
            if isinstance(backup_filename_or_path, Path):
                zip_path = backup_filename_or_path
            else:
                zip_path = self.backup_dir / backup_filename_or_path

            if not zip_path.exists():
                return False, f"Backup file '{zip_path.name}' does not exist."

            # Verify integrity
            with zipfile.ZipFile(zip_path, "r") as zf:
                test_result = zf.testzip()
                if test_result is not None:
                    return False, f"Corrupted backup archive: file '{test_result}' is invalid."
                namelist = zf.namelist()

            # Create pre-restore safety backup
            self.create_backup(note="pre_restore_safety")

            # Extract into temporary folder first, then copy files to data_dir
            temp_extract_dir = self.backup_dir / f"restore_temp_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            temp_extract_dir.mkdir(parents=True, exist_ok=True)

            try:
                with zipfile.ZipFile(zip_path, "r") as zf:
                    zf.extractall(temp_extract_dir)

                # Move extracted files to DATA_DIR
                restored_count = 0
                for item in temp_extract_dir.glob("*.csv"):
                    dest = self.data_dir / item.name
                    shutil.copy2(item, dest)
                    restored_count += 1

                msg = f"Successfully restored {restored_count} datasets from '{zip_path.name}'."
                logger.info(msg)
                return True, msg
            finally:
                if temp_extract_dir.exists():
                    shutil.rmtree(temp_extract_dir, ignore_errors=True)

        except Exception as e:
            err_msg = f"Failed to restore backup: {str(e)}"
            logger.error(err_msg)
            return False, err_msg

