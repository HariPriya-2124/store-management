"""
Storage Manager module for Store Management System.
Provides a clean storage abstraction layer, thread-safe data operations,
atomic multi-table transactions, and referential integrity enforcement.
Allows future transition to SQLite without changing application module logic.
"""

import threading
from datetime import date, datetime
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from typing import Dict, List, Optional, Tuple
import pandas as pd

from config import DATA_DIR
from database.backup_manager import BackupManager
from database.csv_handler import (
    SCHEMAS,
    classify_alert_status,
    generate_synthetic_datasets,
    read_csv_safe,
    write_csv_atomic,
)
from utils.helpers import calculate_days_until, generate_next_id, safe_float, safe_int
from utils.logger import get_logger

logger = get_logger("StorageManager")


class StorageManager:
    """
    Central storage manager implementing the Data Access Object (DAO) pattern.
    Maintains clean separation between file I/O, schemas, and UI modules.
    Supports customizable data and backup directories for test isolation.
    """

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        backup_dir: Optional[Path] = None,
        auto_init: bool = True
    ):
        self._lock = threading.RLock()
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.products_file = self.data_dir / "products.csv"
        self.suppliers_file = self.data_dir / "suppliers.csv"
        self.sales_file = self.data_dir / "sales.csv"
        self.stock_movements_file = self.data_dir / "stock_movements.csv"
        self.expiry_alerts_file = self.data_dir / "expiry_alerts.csv"
        self.sms_logs_file = self.data_dir / "sms_logs.csv"

        self.backup_mgr = BackupManager(backup_dir=backup_dir, data_dir=self.data_dir)

        if auto_init:
            self.initialize_storage()

    def initialize_storage(self, force_regenerate: bool = False) -> None:
        """Initializes datasets if missing, and syncs expiry alerts."""
        with self._lock:
            generate_synthetic_datasets(target_data_dir=self.data_dir, force_regenerate=force_regenerate)
            self.refresh_expiry_alerts()

    # =========================================================================
    # CORE GETTERS (READ-ONLY DATAFRAMES)
    # =========================================================================

    def get_products(self) -> pd.DataFrame:
        """Returns products DataFrame with proper columns and types."""
        with self._lock:
            df = read_csv_safe(self.products_file, SCHEMAS["products"])
            return df.copy()

    def get_suppliers(self) -> pd.DataFrame:
        """Returns suppliers DataFrame."""
        with self._lock:
            df = read_csv_safe(self.suppliers_file, SCHEMAS["suppliers"])
            return df.copy()

    def get_sales(self) -> pd.DataFrame:
        """Returns sales transactions DataFrame."""
        with self._lock:
            df = read_csv_safe(self.sales_file, SCHEMAS["sales"])
            return df.copy()

    def get_stock_movements(self) -> pd.DataFrame:
        """Returns stock movements DataFrame."""
        with self._lock:
            df = read_csv_safe(self.stock_movements_file, SCHEMAS["stock_movements"])
            return df.copy()

    def get_expiry_alerts(self) -> pd.DataFrame:
        """Returns expiry alerts DataFrame."""
        with self._lock:
            df = read_csv_safe(self.expiry_alerts_file, SCHEMAS["expiry_alerts"])
            return df.copy()

    def get_sms_logs(self) -> pd.DataFrame:
        """Returns dispatched SMS history DataFrame."""
        with self._lock:
            df = read_csv_safe(self.sms_logs_file, SCHEMAS["sms_logs"])
            return df.copy()

    def record_sms_log(self, sms_data: Dict[str, any]) -> Tuple[bool, str]:
        """Appends an SMS dispatch record to persistent logs."""
        with self._lock:
            try:
                df = self.get_sms_logs()
                new_row = {col: str(sms_data.get(col, "")) for col in SCHEMAS["sms_logs"]}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                if write_csv_atomic(self.sms_logs_file, df):
                    return True, "SMS logged successfully."
                return False, "Failed to save SMS log."
            except Exception as e:
                logger.error(f"Error recording SMS log: {e}")
                return False, str(e)

    # =========================================================================
    # PRODUCT OPERATIONS
    # =========================================================================

    def add_product(self, product_data: Dict[str, any]) -> Tuple[bool, str]:
        """
        Adds a new product, records initial stock movement, and creates expiry alert.
        """
        with self._lock:
            try:
                df_prod = self.get_products()
                pid = str(product_data["product_id"]).strip().upper()

                if not df_prod.empty and pid in df_prod["product_id"].values:
                    return False, f"Product ID '{pid}' already exists."

                # Verify supplier reference
                df_supp = self.get_suppliers()
                sid = str(product_data["supplier_id"]).strip().upper()
                if not df_supp.empty and sid not in df_supp["supplier_id"].values:
                    return False, f"Supplier ID '{sid}' does not exist in suppliers database."

                new_row = {col: str(product_data.get(col, "")) for col in SCHEMAS["products"]}
                df_prod = pd.concat([df_prod, pd.DataFrame([new_row])], ignore_index=True)

                if not write_csv_atomic(self.products_file, df_prod):
                    return False, "Failed to write product data to storage."

                # Record INITIAL_STOCK movement if quantity > 0
                stock_qty = safe_int(product_data.get("stock_quantity", 0))
                if stock_qty > 0:
                    df_mov = self.get_stock_movements()
                    mov_id = generate_next_id("MOV-", df_mov["movement_id"].tolist() if not df_mov.empty else [])
                    mov_row = {
                        "movement_id": mov_id,
                        "product_id": pid,
                        "movement_date": date.today().strftime("%Y-%m-%d"),
                        "movement_type": "INITIAL_STOCK",
                        "quantity_change": str(stock_qty),
                        "notes": "Initial stock entry on product registration",
                    }
                    df_mov = pd.concat([df_mov, pd.DataFrame([mov_row])], ignore_index=True)
                    write_csv_atomic(self.stock_movements_file, df_mov)

                # Sync expiry alerts
                self.refresh_expiry_alerts()

                logger.info(f"Product '{pid}' ({product_data.get('product_name')}) added successfully.")
                return True, f"Product '{pid}' added successfully."

            except Exception as e:
                logger.error(f"Error in add_product: {e}")
                return False, f"Error adding product: {str(e)}"

    def update_product(self, product_id: str, updated_data: Dict[str, any]) -> Tuple[bool, str]:
        """Updates an existing product's details."""
        with self._lock:
            try:
                df_prod = self.get_products()
                pid = str(product_id).strip().upper()

                if df_prod.empty or pid not in df_prod["product_id"].values:
                    return False, f"Product '{pid}' not found."

                # Verify supplier reference
                df_supp = self.get_suppliers()
                sid = str(updated_data.get("supplier_id", "")).strip().upper()
                if sid and not df_supp.empty and sid not in df_supp["supplier_id"].values:
                    return False, f"Supplier ID '{sid}' does not exist."

                idx = df_prod.index[df_prod["product_id"] == pid].tolist()[0]
                for col in SCHEMAS["products"]:
                    if col in updated_data and col != "product_id":
                        df_prod.at[idx, col] = str(updated_data[col])

                if not write_csv_atomic(self.products_file, df_prod):
                    return False, "Failed to save updated product to disk."

                self.refresh_expiry_alerts()
                logger.info(f"Product '{pid}' updated successfully.")
                return True, f"Product '{pid}' updated successfully."

            except Exception as e:
                logger.error(f"Error updating product '{product_id}': {e}")
                return False, f"Error updating product: {str(e)}"

    def delete_product(self, product_id: str) -> Tuple[bool, str]:
        """
        Deletes a product, removing associated expiry alert records.
        """
        with self._lock:
            try:
                df_prod = self.get_products()
                pid = str(product_id).strip().upper()

                if df_prod.empty or pid not in df_prod["product_id"].values:
                    return False, f"Product '{pid}' not found."

                # Create safety backup before deletion
                self.backup_mgr.create_backup(note=f"pre_del_prod_{pid}")

                # Remove from products
                df_prod = df_prod[df_prod["product_id"] != pid]
                write_csv_atomic(self.products_file, df_prod)

                # Remove from expiry alerts
                df_exp = self.get_expiry_alerts()
                if not df_exp.empty:
                    df_exp = df_exp[df_exp["product_id"] != pid]
                    write_csv_atomic(self.expiry_alerts_file, df_exp)

                logger.info(f"Product '{pid}' deleted successfully.")
                return True, f"Product '{pid}' deleted successfully."

            except Exception as e:
                logger.error(f"Error deleting product '{product_id}': {e}")
                return False, f"Error deleting product: {str(e)}"

    # =========================================================================
    # SUPPLIER OPERATIONS & REFERENTIAL INTEGRITY
    # =========================================================================

    def add_supplier(self, supplier_data: Dict[str, any]) -> Tuple[bool, str]:
        """Adds a new supplier."""
        with self._lock:
            try:
                df_supp = self.get_suppliers()
                sid = str(supplier_data["supplier_id"]).strip().upper()

                if not df_supp.empty and sid in df_supp["supplier_id"].values:
                    return False, f"Supplier ID '{sid}' already exists."

                new_row = {col: str(supplier_data.get(col, "")) for col in SCHEMAS["suppliers"]}
                df_supp = pd.concat([df_supp, pd.DataFrame([new_row])], ignore_index=True)

                if not write_csv_atomic(self.suppliers_file, df_supp):
                    return False, "Failed to save supplier."

                logger.info(f"Supplier '{sid}' added successfully.")
                return True, f"Supplier '{sid}' added successfully."
            except Exception as e:
                logger.error(f"Error adding supplier: {e}")
                return False, f"Error adding supplier: {str(e)}"

    def update_supplier(self, supplier_id: str, updated_data: Dict[str, any]) -> Tuple[bool, str]:
        """Updates an existing supplier's details."""
        with self._lock:
            try:
                df_supp = self.get_suppliers()
                sid = str(supplier_id).strip().upper()

                if df_supp.empty or sid not in df_supp["supplier_id"].values:
                    return False, f"Supplier '{sid}' not found."

                idx = df_supp.index[df_supp["supplier_id"] == sid].tolist()[0]
                for col in SCHEMAS["suppliers"]:
                    if col in updated_data and col != "supplier_id":
                        df_supp.at[idx, col] = str(updated_data[col])

                if not write_csv_atomic(self.suppliers_file, df_supp):
                    return False, "Failed to save supplier updates."

                logger.info(f"Supplier '{sid}' updated successfully.")
                return True, f"Supplier '{sid}' updated successfully."
            except Exception as e:
                logger.error(f"Error updating supplier '{supplier_id}': {e}")
                return False, f"Error updating supplier: {str(e)}"

    def delete_supplier(self, supplier_id: str) -> Tuple[bool, str]:
        """
        Safely deletes a supplier.
        PREVENTS deletion if any product references this supplier to maintain foreign key integrity.
        """
        with self._lock:
            try:
                sid = str(supplier_id).strip().upper()
                df_supp = self.get_suppliers()

                if df_supp.empty or sid not in df_supp["supplier_id"].values:
                    return False, f"Supplier '{sid}' not found."

                # Referential Integrity Check
                df_prod = self.get_products()
                if not df_prod.empty and "supplier_id" in df_prod.columns:
                    linked = df_prod[df_prod["supplier_id"] == sid]
                    if not linked.empty:
                        linked_pids = linked["product_id"].tolist()
                        return False, (
                            f"Cannot delete supplier '{sid}'! It is linked to {len(linked)} product(s): "
                            f"{', '.join(linked_pids[:4])}{'...' if len(linked_pids) > 4 else ''}. "
                            f"Please reassign these products to another supplier first."
                        )

                # Safe to delete
                self.backup_mgr.create_backup(note=f"pre_del_supp_{sid}")
                df_supp = df_supp[df_supp["supplier_id"] != sid]
                write_csv_atomic(self.suppliers_file, df_supp)

                logger.info(f"Supplier '{sid}' deleted successfully.")
                return True, f"Supplier '{sid}' deleted successfully."
            except Exception as e:
                logger.error(f"Error deleting supplier '{supplier_id}': {e}")
                return False, f"Error deleting supplier: {str(e)}"

    def get_supplier_products(self, supplier_id: str) -> pd.DataFrame:
        """Returns all products linked to a specific supplier."""
        with self._lock:
            sid = str(supplier_id).strip().upper()
            df_prod = self.get_products()
            if df_prod.empty or "supplier_id" not in df_prod.columns:
                return pd.DataFrame(columns=SCHEMAS["products"])
            return df_prod[df_prod["supplier_id"] == sid].copy()

    # =========================================================================
    # ATOMIC SALES TRANSACTIONS
    # =========================================================================

    def record_sale(
        self,
        product_id: str,
        quantity: int,
        unit_price: float,
        sale_date: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict[str, any]]]:
        """
        Executes an atomic sales transaction:
        1. Validates product exists and available stock >= quantity.
        2. Calculates total_amount = quantity * unit_price.
        3. Generates unique transaction ID.
        4. Decreases product stock_quantity in Products.
        5. Records sale record in Sales.
        6. Records 'SALE' movement (-quantity) in Stock Movements.
        7. Atomically saves all modified datasets. If any step fails, rolls back.
        """
        with self._lock:
            try:
                pid = str(product_id).strip().upper()
                qty = int(quantity)
                if qty <= 0:
                    return False, "Sale quantity must be at least 1.", None

                df_prod = self.get_products()
                if df_prod.empty or pid not in df_prod["product_id"].values:
                    return False, f"Product '{pid}' not found.", None

                idx = df_prod.index[df_prod["product_id"] == pid].tolist()[0]
                current_stock = safe_int(df_prod.at[idx, "stock_quantity"])

                if qty > current_stock:
                    return False, f"Insufficient stock for '{pid}'! Available: {current_stock}, Requested: {qty}.", None

                # Keep snapshot of old DataFrames for rollback
                old_prod = df_prod.copy()
                df_sales = self.get_sales()
                old_sales = df_sales.copy()
                df_mov = self.get_stock_movements()
                old_mov = df_mov.copy()

                # 1. Update product stock
                new_stock = current_stock - qty
                df_prod.at[idx, "stock_quantity"] = str(new_stock)

                # 2. Append sale record
                txn_id = generate_next_id("TXN-", df_sales["transaction_id"].tolist() if not df_sales.empty else [])
                date_str = sale_date or date.today().strftime("%Y-%m-%d")
                total_amount = round(qty * unit_price, 2)

                sale_entry = {
                    "transaction_id": txn_id,
                    "product_id": pid,
                    "sale_date": date_str,
                    "quantity": str(qty),
                    "unit_price": f"{unit_price:.2f}",
                    "total_amount": f"{total_amount:.2f}",
                }
                df_sales = pd.concat([df_sales, pd.DataFrame([sale_entry])], ignore_index=True)

                # 3. Append stock movement record
                mov_id = generate_next_id("MOV-", df_mov["movement_id"].tolist() if not df_mov.empty else [])
                mov_entry = {
                    "movement_id": mov_id,
                    "product_id": pid,
                    "movement_date": date_str,
                    "movement_type": "SALE",
                    "quantity_change": str(-qty),
                    "notes": f"POS Sale transaction {txn_id}",
                }
                df_mov = pd.concat([df_mov, pd.DataFrame([mov_entry])], ignore_index=True)

                # 4. Atomic multi-file write
                success_prod = write_csv_atomic(self.products_file, df_prod)
                success_sales = write_csv_atomic(self.sales_file, df_sales)
                success_mov = write_csv_atomic(self.stock_movements_file, df_mov)

                if not (success_prod and success_sales and success_mov):
                    # Rollback
                    logger.error("Atomic transaction failed. Rolling back files...")
                    write_csv_atomic(self.products_file, old_prod)
                    write_csv_atomic(self.sales_file, old_sales)
                    write_csv_atomic(self.stock_movements_file, old_mov)
                    return False, "Transaction write failure. Changes were rolled back.", None

                # Update expiry alerts affected quantity
                self._update_expiry_qty_for_product(pid, new_stock)

                receipt = {
                    "transaction_id": txn_id,
                    "product_id": pid,
                    "product_name": df_prod.at[idx, "product_name"],
                    "sale_date": date_str,
                    "quantity": qty,
                    "unit_price": unit_price,
                    "total_amount": total_amount,
                    "remaining_stock": new_stock,
                }
                logger.info(f"Sale recorded successfully: {txn_id} for product {pid} (Qty: {qty}, Total: ₹{total_amount:.2f})")
                return True, f"Sale {txn_id} completed successfully.", receipt

            except Exception as e:
                logger.error(f"Unexpected error in record_sale: {e}")
                return False, f"Sale execution error: {str(e)}", None

    # =========================================================================
    # INVENTORY & STOCK MOVEMENTS
    # =========================================================================

    def record_stock_movement(
        self,
        product_id: str,
        movement_type: str,
        quantity_change: int,
        notes: str = ""
    ) -> Tuple[bool, str]:
        """
        Records a stock movement (PURCHASE_RECEIPT, DAMAGED_WRITE_OFF, MANUAL_ADJUSTMENT, RETURN)
        and adjusts product stock accordingly.
        """
        with self._lock:
            try:
                pid = str(product_id).strip().upper()
                df_prod = self.get_products()

                if df_prod.empty or pid not in df_prod["product_id"].values:
                    return False, f"Product '{pid}' not found."

                idx = df_prod.index[df_prod["product_id"] == pid].tolist()[0]
                current_stock = safe_int(df_prod.at[idx, "stock_quantity"])
                new_stock = current_stock + int(quantity_change)

                if new_stock < 0:
                    return False, (
                        f"Stock movement would result in negative stock balance! "
                        f"Current: {current_stock}, Change: {quantity_change}, Result: {new_stock}."
                    )

                old_prod = df_prod.copy()
                df_mov = self.get_stock_movements()
                old_mov = df_mov.copy()

                # Update product stock
                df_prod.at[idx, "stock_quantity"] = str(new_stock)

                # Append movement
                mov_id = generate_next_id("MOV-", df_mov["movement_id"].tolist() if not df_mov.empty else [])
                mov_entry = {
                    "movement_id": mov_id,
                    "product_id": pid,
                    "movement_date": date.today().strftime("%Y-%m-%d"),
                    "movement_type": str(movement_type).upper(),
                    "quantity_change": str(quantity_change),
                    "notes": str(notes).strip() or f"{movement_type} operation",
                }
                df_mov = pd.concat([df_mov, pd.DataFrame([mov_entry])], ignore_index=True)

                if not (write_csv_atomic(self.products_file, df_prod) and write_csv_atomic(self.stock_movements_file, df_mov)):
                    # Rollback
                    write_csv_atomic(self.products_file, old_prod)
                    write_csv_atomic(self.stock_movements_file, old_mov)
                    return False, "Failed to record stock movement to disk. Rolled back."

                self._update_expiry_qty_for_product(pid, new_stock)
                msg = f"Stock movement {mov_id} ({movement_type}) recorded for '{pid}'. New Stock: {new_stock}."
                logger.info(msg)
                return True, msg

            except Exception as e:
                logger.error(f"Error recording stock movement: {e}")
                return False, f"Error recording stock movement: {str(e)}"

    def manual_stock_reconciliation(
        self,
        product_id: str,
        physical_count: int,
        reason: str
    ) -> Tuple[bool, str]:
        """
        Sets a product's stock to the verified physical inventory count,
        calculating and logging the variance as a MANUAL_ADJUSTMENT.
        """
        with self._lock:
            try:
                pid = str(product_id).strip().upper()
                df_prod = self.get_products()
                if df_prod.empty or pid not in df_prod["product_id"].values:
                    return False, f"Product '{pid}' not found."

                idx = df_prod.index[df_prod["product_id"] == pid].tolist()[0]
                current_stock = safe_int(df_prod.at[idx, "stock_quantity"])
                variance = physical_count - current_stock

                if variance == 0:
                    return True, "Physical count matches recorded stock. No adjustment needed."

                note = f"Physical Audit: Counted {physical_count} vs System {current_stock} (Diff: {variance:+d}). Reason: {reason}"
                return self.record_stock_movement(pid, "MANUAL_ADJUSTMENT", variance, notes=note)

            except Exception as e:
                logger.error(f"Error in manual stock reconciliation: {e}")
                return False, f"Reconciliation error: {str(e)}"

    # =========================================================================
    # EXPIRY ALERT SYSTEM
    # =========================================================================

    def refresh_expiry_alerts(self) -> pd.DataFrame:
        """
        Recalculates days_until_expiry and alert_status for all products based on the current date.
        Updates the expiry_alerts CSV file.
        """
        with self._lock:
            try:
                df_prod = self.get_products()
                if df_prod.empty:
                    df_empty = pd.DataFrame(columns=SCHEMAS["expiry_alerts"])
                    write_csv_atomic(self.expiry_alerts_file, df_empty)
                    return df_empty

                df_exp = self.get_expiry_alerts()
                existing_map = {}
                if not df_exp.empty:
                    for _, r in df_exp.iterrows():
                        existing_map[r["product_id"]] = {
                            "alert_id": r.get("alert_id", ""),
                            "batch_number": r.get("batch_number", ""),
                            "notification_sent": r.get("notification_sent", "Pending"),
                        }

                today = date.today()
                alert_rows = []
                alt_counter = 1001

                for _, p in df_prod.iterrows():
                    pid = p["product_id"]
                    exp_date_str = p["expiry_date"]
                    days_left = calculate_days_until(exp_date_str, today)
                    status = classify_alert_status(days_left)
                    qty = safe_int(p["stock_quantity"])

                    if pid in existing_map:
                        alt_id = existing_map[pid]["alert_id"]
                        batch = existing_map[pid]["batch_number"]
                        notif = existing_map[pid]["notification_sent"]
                    else:
                        alt_id = f"ALT-{alt_counter}"
                        alt_counter += 1
                        batch = f"BCH-{abs(hash(pid)) % 9000 + 1000}"
                        notif = "Sent" if status in ["EXPIRED", "EXPIRING_SOON_7"] else "Pending"

                    alert_rows.append({
                        "alert_id": alt_id,
                        "product_id": pid,
                        "batch_number": batch,
                        "expiry_date": exp_date_str,
                        "quantity_affected": str(qty),
                        "days_until_expiry": str(days_left),
                        "alert_status": status,
                        "notification_sent": notif,
                    })

                df_refreshed = pd.DataFrame(alert_rows, columns=SCHEMAS["expiry_alerts"])
                write_csv_atomic(self.expiry_alerts_file, df_refreshed)
                return df_refreshed

            except Exception as e:
                logger.error(f"Error refreshing expiry alerts: {e}")
                return self.get_expiry_alerts()

    def update_alert_notification(self, alert_id: str, new_status: str = "Sent") -> Tuple[bool, str]:
        """Marks notification_sent as 'Sent' or 'Dismissed' for an alert."""
        with self._lock:
            try:
                df_exp = self.get_expiry_alerts()
                aid = str(alert_id).strip().upper()
                if df_exp.empty or aid not in df_exp["alert_id"].values:
                    return False, f"Alert '{aid}' not found."

                idx = df_exp.index[df_exp["alert_id"] == aid].tolist()[0]
                df_exp.at[idx, "notification_sent"] = new_status
                write_csv_atomic(self.expiry_alerts_file, df_exp)
                return True, f"Alert '{aid}' marked as {new_status}."
            except Exception as e:
                return False, str(e)

    def _update_expiry_qty_for_product(self, product_id: str, new_qty: int) -> None:
        """Helper to keep quantity_affected in expiry_alerts synced."""
        try:
            df_exp = self.get_expiry_alerts()
            if not df_exp.empty and product_id in df_exp["product_id"].values:
                idx = df_exp.index[df_exp["product_id"] == product_id].tolist()[0]
                df_exp.at[idx, "quantity_affected"] = str(new_qty)
                write_csv_atomic(self.expiry_alerts_file, df_exp)
        except Exception as e:
            logger.warning(f"Failed to sync expiry quantity for {product_id}: {e}")
