
"""
Expiry Notification System Module for Store Management System.
Automatically monitors product shelf life, classifies items into risk tiers,
provides in-app alert tracking, disposal workflows, and audit reporting.
"""

from datetime import date
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pandas as pd

from config import FONTS, THEME
from database.storage_manager import StorageManager
from utils.helpers import export_dataframe_to_csv, safe_int
from utils.logger import get_logger

logger = get_logger("ExpiryAlertsModule")


class ExpiryAlertsView(ttk.Frame):
    """
    Expiry Alert Management View providing status categorization,
    notification tracking, direct write-off disposal actions, and reporting.
    """

    def __init__(
        self,
        parent: tk.Widget,
        storage: StorageManager,
        on_disposal_completed=None,
        nav_callback=None
    ):
        super().__init__(parent)

        self.storage = storage
        self.on_disposal_completed = on_disposal_completed
        self.nav_callback = nav_callback

        self.df_alerts = pd.DataFrame()
        self.df_products = pd.DataFrame()

        self._build_ui()
        self.load_alerts()

    # =========================================================================
    # USER INTERFACE
    # =========================================================================

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # Top Header & Action Bar
        top_frame = tk.Frame(self, bg=THEME["gray_bg"])
        top_frame.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=20,
            pady=(15, 8)
        )

        lbl_title = tk.Label(
            top_frame,
            text="Product Expiry & Shelf-Life Monitoring",
            font=FONTS["h1"],
            bg=THEME["gray_bg"],
            fg=THEME["text_primary"],
        )
        lbl_title.pack(side="left")

        # Back to hub button
        if self.nav_callback:
            tk.Button(
                top_frame,
                text="← Back to CRUD Operations",
                command=lambda: self.nav_callback("hub"),
                bg=THEME.get("turquoise", "#028090"),
                fg=THEME["white"],
                font=FONTS["caption_bold"],
                relief="flat",
                padx=10,
                pady=3,
                cursor="hand2",
            ).pack(side="left", padx=(12, 0))

        actions_frame = tk.Frame(
            top_frame,
            bg=THEME["gray_bg"]
        )
        actions_frame.pack(side="right")

        btn_refresh = tk.Button(
            actions_frame,
            text="🔄 Re-calculate Expiry Status",
            command=self._refresh_calculations,
            bg=THEME["navy_accent"],
            fg=THEME["white"],
            font=FONTS["caption_bold"],
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
        )
        btn_refresh.pack(side="left", padx=4)

        btn_export = tk.Button(
            actions_frame,
            text="📥 Export Expiry CSV",
            command=self._export_expiry_csv,
            bg=THEME["white"],
            fg=THEME["navy_accent"],
            bd=1,
            relief="solid",
            font=FONTS["caption_bold"],
            padx=10,
            pady=4,
            cursor="hand2",
        )
        btn_export.pack(side="left", padx=4)

        # Risk Status Summary Cards
        self.cards_frame = tk.Frame(
            self,
            bg=THEME["gray_bg"]
        )
        self.cards_frame.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=20,
            pady=(0, 10)
        )

        for i in range(4):
            self.cards_frame.columnconfigure(i, weight=1)

        # Main Filter & Table Frame
        main_content = tk.Frame(
            self,
            bg=THEME["gray_bg"]
        )
        main_content.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=20,
            pady=(0, 15)
        )

        main_content.columnconfigure(0, weight=1)
        main_content.rowconfigure(1, weight=1)

        # Filter Bar
        filter_bar = tk.Frame(
            main_content,
            bg=THEME["white"],
            bd=1,
            relief="solid",
            padx=10,
            pady=8
        )
        filter_bar.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 8)
        )

        tk.Label(
            filter_bar,
            text="🔍 Search:",
            font=FONTS["body_bold"],
            bg=THEME["white"]
        ).pack(side="left", padx=(0, 5))

        self.entry_search = ttk.Entry(
            filter_bar,
            width=24
        )
        self.entry_search.pack(
            side="left",
            padx=(0, 15)
        )
        self.entry_search.bind(
            "<KeyRelease>",
            lambda e: self.filter_alerts()
        )

        tk.Label(
            filter_bar,
            text="Status Filter:",
            font=FONTS["body_bold"],
            bg=THEME["white"]
        ).pack(side="left", padx=(0, 5))

        self.combo_status = ttk.Combobox(
            filter_bar,
            state="readonly",
            values=[
                "All Alerts",
                "EXPIRED Only",
                "Expiring within 7 Days",
                "Expiring within 30 Days",
                "SAFE Stock Only"
            ],
            width=22
        )

        self.combo_status.set("All Alerts")
        self.combo_status.pack(
            side="left",
            padx=(0, 15)
        )
        self.combo_status.bind(
            "<<ComboboxSelected>>",
            lambda e: self.filter_alerts()
        )

        self.lbl_count = tk.Label(
            filter_bar,
            text="",
            font=FONTS["caption_bold"],
            bg=THEME["white"],
            fg=THEME["text_muted"]
        )
        self.lbl_count.pack(side="right")

        # Expiry Table
        table_frame = tk.Frame(
            main_content,
            bg=THEME["white"],
            bd=1,
            relief="solid"
        )
        table_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            pady=(0, 10)
        )

        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        cols = (
            "alert_id",
            "product_id",
            "product_name",
            "batch",
            "expiry_date",
            "days_left",
            "affected_qty",
            "status",
            "notif"
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=cols,
            show="headings",
            selectmode="browse"
        )

        headers = {
            "alert_id": ("Alert ID", 80, "center"),
            "product_id": ("Product ID", 80, "center"),
            "product_name": ("Product Name", 210, "w"),
            "batch": ("Batch Number", 100, "center"),
            "expiry_date": ("Expiry Date", 90, "center"),
            "days_left": ("Days Remaining", 100, "center"),
            "affected_qty": ("Units Affected", 95, "center"),
            "status": ("Risk Classification", 130, "center"),
            "notif": ("Notification Status", 115, "center"),
        }

        for col, (text, width, anchor) in headers.items():
            self.tree.heading(col, text=text)
            self.tree.column(
                col,
                width=width,
                anchor=anchor
            )

        # Risk Status Styling
        self.tree.tag_configure(
            "expired",
            background=THEME["danger_bg"]
        )
        self.tree.tag_configure(
            "warn7",
            background=THEME["warning_bg"]
        )
        self.tree.tag_configure(
            "warn30",
            background="#FEF9C3"
        )
        self.tree.tag_configure(
            "safe",
            background=THEME["white"]
        )

        sb = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=sb.set
        )

        self.tree.grid(
            row=0,
            column=0,
            sticky="nsew"
        )
        sb.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        # Bottom Actions Bar
        btm_bar = tk.Frame(
            main_content,
            bg=THEME["gray_bg"]
        )
        btm_bar.grid(
            row=2,
            column=0,
            sticky="ew"
        )

        btn_mark_sent = tk.Button(
            btm_bar,
            text="✉️ Acknowledge / Mark Notification Sent",
            command=self._mark_notification_sent,
            bg=THEME["navy_accent"],
            fg=THEME["white"],
            font=FONTS["caption_bold"],
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2"
        )
        btn_mark_sent.pack(
            side="left",
            padx=(0, 6)
        )

        btn_dispose = tk.Button(
            btm_bar,
            text="🗑️ Initiate Stock Disposal (Write-Off)",
            command=self._initiate_disposal,
            bg=THEME["danger"],
            fg=THEME["white"],
            font=FONTS["caption_bold"],
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2"
        )
        btn_dispose.pack(
            side="left",
            padx=6
        )

        # Risk Legend
        legend_box = tk.Frame(
            btm_bar,
            bg=THEME["gray_bg"]
        )
        legend_box.pack(side="right")

        tk.Label(
            legend_box,
            text="  EXPIRED (<=0d)  ",
            bg=THEME["danger_bg"],
            fg=THEME["danger"],
            font=FONTS["caption_bold"]
        ).pack(side="left", padx=3)

        tk.Label(
            legend_box,
            text="  URGENT (1-7d)  ",
            bg=THEME["warning_bg"],
            fg=THEME["warning"],
            font=FONTS["caption_bold"]
        ).pack(side="left", padx=3)

        tk.Label(
            legend_box,
            text="  CAUTION (8-30d)  ",
            bg="#FEF9C3",
            fg="#854D0E",
            font=FONTS["caption_bold"]
        ).pack(side="left", padx=3)

        tk.Label(
            legend_box,
            text="  SAFE (>30d)  ",
            bg=THEME["success_bg"],
            fg=THEME["success"],
            font=FONTS["caption_bold"]
        ).pack(side="left", padx=3)

    # =========================================================================
    # LOAD ALERT DATA
    # =========================================================================

    def load_alerts(self):
        """Loads alert data and product names."""

        try:
            self.df_alerts = self.storage.get_expiry_alerts()
            self.df_products = self.storage.get_products()

            self.filter_alerts()

        except Exception as exc:
            logger.exception(
                "Unable to load expiry alerts: %s",
                exc
            )

            messagebox.showerror(
                "Expiry Alert Error",
                f"Unable to load expiry alerts:\n{exc}",
                parent=self
            )

    # =========================================================================
    # REFRESH EXPIRY CALCULATIONS
    # =========================================================================

    def _refresh_calculations(self):
        """Forces recalculation against today's date."""

        try:
            self.df_alerts = self.storage.refresh_expiry_alerts()
            self.df_products = self.storage.get_products()

            self.filter_alerts()

            messagebox.showinfo(
                "Refreshed",
                "Expiry calculations successfully refreshed.",
                parent=self
            )

        except Exception as exc:
            logger.exception(
                "Expiry calculation refresh failed: %s",
                exc
            )

            messagebox.showerror(
                "Refresh Failed",
                str(exc),
                parent=self
            )

    # =========================================================================
    # FILTER AND DISPLAY ALERTS
    # =========================================================================

    def filter_alerts(self):
        """Filters table based on search query and status filter."""

        for item in self.tree.get_children():
            self.tree.delete(item)

        if self.df_alerts.empty:
            self._render_cards(0, 0, 0, 0)
            self.lbl_count.config(text="0 alerts")
            return

        df = self.df_alerts.copy()

        # Ensure expected columns exist
        required_defaults = {
            "alert_id": "",
            "product_id": "",
            "product_name": "Unknown",
            "batch_number": "",
            "expiry_date": "",
            "days_until_expiry": 999,
            "quantity_affected": 0,
            "alert_status": "SAFE",
            "notification_sent": "Not Sent"
        }

        for column, default in required_defaults.items():
            if column not in df.columns:
                df[column] = default

        # Convert days remaining to numeric
        df["days_num"] = (
            pd.to_numeric(
                df["days_until_expiry"],
                errors="coerce"
            )
            .fillna(999)
            .astype(int)
        )

        # Map product names using product IDs
        if (
            not self.df_products.empty
            and "product_id" in self.df_products.columns
            and "product_name" in self.df_products.columns
        ):

            name_map = dict(
                zip(
                    self.df_products["product_id"].astype(str),
                    self.df_products["product_name"]
                )
            )

            df["product_name"] = (
                df["product_name"]
                .replace("", pd.NA)
                .fillna(
                    df["product_id"].astype(str).map(name_map)
                )
            )

        df["product_name"] = (
            df["product_name"]
            .fillna("Unknown")
        )

        # Search Query
        q = self.entry_search.get().strip().lower()

        if q:
            search_columns = [
                "alert_id",
                "product_id",
                "product_name",
                "batch_number"
            ]

            mask = pd.Series(
                False,
                index=df.index
            )

            for column in search_columns:
                mask |= (
                    df[column]
                    .fillna("")
                    .astype(str)
                    .str.lower()
                    .str.contains(q, na=False)
                )

            df = df[mask]

        # Status Filter
        st = self.combo_status.get()

        if st == "EXPIRED Only":
            df = df[
                (df["alert_status"] == "EXPIRED")
                | (df["days_num"] <= 0)
            ]

        elif st == "Expiring within 7 Days":
            df = df[
                (df["days_num"] >= 1)
                & (df["days_num"] <= 7)
            ]

        elif st == "Expiring within 30 Days":
            df = df[
                (df["days_num"] >= 8)
                & (df["days_num"] <= 30)
            ]

        elif st == "SAFE Stock Only":
            df = df[df["days_num"] > 30]

        # Sort: Expired first, then closest expiry
        df = df.sort_values(
            by="days_num",
            ascending=True
        )

        # Populate Treeview
        for _, row in df.iterrows():

            days = safe_int(row["days_num"])
            status_code = str(row["alert_status"]).upper()

            tag = "safe"
            display_status = "SAFE (>30 days)"

            if status_code == "EXPIRED" or days <= 0:
                tag = "expired"

                if days < 0:
                    display_status = f"EXPIRED ({abs(days)}d ago)"
                else:
                    display_status = "EXPIRED (0d)"

            elif status_code == "EXPIRING_SOON_7" or days <= 7:
                tag = "warn7"
                display_status = f"CRITICAL ({days}d left)"

            elif status_code == "EXPIRING_SOON_30" or days <= 30:
                tag = "warn30"
                display_status = f"WARNING ({days}d left)"

            self.tree.insert(
                "",
                "end",
                values=(
                    row["alert_id"],
                    row["product_id"],
                    row["product_name"],
                    row["batch_number"],
                    row["expiry_date"],
                    (
                        f"{days} days"
                        if days >= 0
                        else f"{days} days (Past)"
                    ),
                    row["quantity_affected"],
                    display_status,
                    row["notification_sent"],
                ),
                tags=(tag,),
            )

        # Calculate summary counts across all alerts
        all_days = (
            pd.to_numeric(
                self.df_alerts.get(
                    "days_until_expiry",
                    pd.Series(
                        999,
                        index=self.df_alerts.index
                    )
                ),
                errors="coerce"
            )
            .fillna(999)
        )

        total_exp = int((all_days <= 0).sum())
        total_7 = int(
            ((all_days >= 1) & (all_days <= 7)).sum()
        )
        total_30 = int(
            ((all_days >= 8) & (all_days <= 30)).sum()
        )
        total_safe = int((all_days > 30).sum())

        self._render_cards(
            total_exp,
            total_7,
            total_30,
            total_safe
        )

        self.lbl_count.config(
            text=f"Showing {len(df)} of {len(self.df_alerts)} batches"
        )

    # =========================================================================
    # SUMMARY CARDS
    # =========================================================================

    def _render_cards(
        self,
        expired: int,
        in_7: int,
        in_30: int,
        safe: int
    ):
        """Displays expiry risk summary cards."""

        for widget in self.cards_frame.winfo_children():
            widget.destroy()

        cards = [
            (
                "Expired Stock",
                f"{expired} Products",
                "Requires immediate disposal",
                THEME["danger"]
            ),
            (
                "Expiring in ≤ 7 Days",
                f"{in_7} Products",
                "Mark down or clearance promo",
                THEME["warning"]
            ),
            (
                "Expiring in 8-30 Days",
                f"{in_30} Products",
                "Monitor shelf movement",
                "#CA8A04"
            ),
            (
                "Safe Stock (> 30 Days)",
                f"{safe} Products",
                "Healthy shelf stability",
                THEME["success"]
            ),
        ]

        for i, (title, val, sub, color) in enumerate(cards):

            card = tk.Frame(
                self.cards_frame,
                bg=THEME["white"],
                bd=1,
                relief="solid",
                padx=10,
                pady=6
            )

            card.grid(
                row=0,
                column=i,
                padx=4,
                sticky="ew"
            )

            tk.Label(
                card,
                text=title,
                font=FONTS["card_title"],
                bg=THEME["white"],
                fg=THEME["text_muted"]
            ).pack(anchor="w")

            tk.Label(
                card,
                text=val,
                font=FONTS["card_value"],
                bg=THEME["white"],
                fg=color
            ).pack(anchor="w", pady=(1, 0))

            tk.Label(
                card,
                text=sub,
                font=FONTS["card_sub"],
                bg=THEME["white"],
                fg=THEME["text_muted"]
            ).pack(anchor="w")

    # =========================================================================
    # MARK NOTIFICATION AS SENT
    # =========================================================================

    def _mark_notification_sent(self):
        """Marks selected alert's notification status as Sent / Acknowledged."""

        selected = self.tree.selection()

        if not selected:
            messagebox.showinfo(
                "Selection Required",
                "Please select an alert from the table to acknowledge.",
                parent=self
            )
            return

        values = self.tree.item(
            selected[0],
            "values"
        )

        aid = values[0]

        try:
            ok, msg = self.storage.update_alert_notification(
                aid,
                "Sent"
            )

            if ok:
                messagebox.showinfo(
                    "Acknowledged",
                    msg,
                    parent=self
                )
                self.load_alerts()

            else:
                messagebox.showerror(
                    "Error",
                    msg,
                    parent=self
                )

        except Exception as exc:
            logger.exception(
                "Unable to update notification status: %s",
                exc
            )

            messagebox.showerror(
                "Error",
                str(exc),
                parent=self
            )

    # =========================================================================
    # INITIATE STOCK DISPOSAL
    # =========================================================================

    def _initiate_disposal(self):
        """
        Writes off an expired batch by recording an EXPIRED_DISPOSAL
        stock movement.
        """

        selected = self.tree.selection()

        if not selected:
            messagebox.showinfo(
                "Selection Required",
                "Please select an expired product to write off.",
                parent=self
            )
            return

        values = self.tree.item(
            selected[0],
            "values"
        )

        aid = values[0]
        pid = values[1]
        pname = values[2]
        qty_affected = safe_int(values[6])

        selected_status = str(values[7]).upper()

        if "EXPIRED" not in selected_status:
            messagebox.showwarning(
                "Invalid Selection",
                "Please select an expired product before initiating disposal.",
                parent=self
            )
            return

        if qty_affected <= 0:
            messagebox.showinfo(
                "Zero Stock",
                f"Product '{pname}' ({pid}) already has 0 units in stock. "
                "No disposal needed.",
                parent=self
            )
            return

        confirm = messagebox.askyesno(
            "Confirm Stock Disposal",
            f"Are you sure you want to write off and dispose of "
            f"{qty_affected} units of expired product:\n\n"
            f"'{pname}' ({pid})?\n\n"
            "This will reduce product stock and record an "
            "'EXPIRED_DISPOSAL' stock movement audit record.",
            icon="warning",
            parent=self
        )

        if not confirm:
            return

        try:
            ok, msg = self.storage.record_stock_movement(
                product_id=pid,
                movement_type="EXPIRED_DISPOSAL",
                quantity_change=-qty_affected,
                notes=f"Disposed expired batch via alert {aid}"
            )

            if ok:
                self.storage.update_alert_notification(
                    aid,
                    "Disposed"
                )

                messagebox.showinfo(
                    "Disposal Logged",
                    msg,
                    parent=self
                )

                self.load_alerts()

                if self.on_disposal_completed:
                    self.on_disposal_completed()

            else:
                messagebox.showerror(
                    "Error",
                    msg,
                    parent=self
                )

        except Exception as exc:
            logger.exception(
                "Expiry disposal failed: %s",
                exc
            )

            messagebox.showerror(
                "Disposal Failed",
                str(exc),
                parent=self
            )

    # =========================================================================
    # EXPORT EXPIRY REPORT
    # =========================================================================

    def _export_expiry_csv(self):
        """Exports expiry alert records to CSV."""

        if self.df_alerts.empty:
            messagebox.showinfo(
                "Export",
                "No expiry alerts available to export.",
                parent=self
            )
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ],
            initialfile=(
                f"expiry_alerts_report_"
                f"{date.today().strftime('%Y%m%d')}.csv"
            )
        )

        if not file_path:
            return

        ok, msg = export_dataframe_to_csv(
            self.df_alerts,
            file_path
        )

        if ok:
            messagebox.showinfo(
                "Export Complete",
                msg,
                parent=self
            )
        else:
            messagebox.showerror(
                "Export Failed",
                msg,
                parent=self
            )
