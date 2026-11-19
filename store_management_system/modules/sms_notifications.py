
"""
Operation 6: Send SMS Expiry Notifications Module for Store Management System.
Allows store administrators and managers to dispatch shelf-life alerts,
markdown promotion notices, and supplier return dispatches via simulated SMS.
"""

from datetime import datetime
import tkinter as tk
from tkinter import ttk

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pandas as pd

from config import FONTS, THEME
from database.storage_manager import StorageManager
from utils.logger import get_logger

logger = get_logger("SMSNotifications")


class SMSNotificationView(ttk.Frame):
    """
    Operation 6: SEND SMS – Expiry alert dispatcher and communications console.
    """

    def __init__(
        self,
        parent: tk.Widget,
        storage: StorageManager,
        nav_callback=None
    ):
        super().__init__(parent)

        self.storage = storage
        self.nav_callback = nav_callback
        self.selected_alert = None

        self._build_ui()
        self.load_alerts()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # 1. Top Bar
        top_bar = tk.Frame(self, bg="#05668D", padx=25, pady=10)
        top_bar.grid(row=0, column=0, sticky="ew")

        tk.Label(
            top_bar,
            text="📱   S E N D   E X P I R Y   N O T I F I C A T I O N S   ( S M S )",
            font=FONTS["h2"],
            bg="#05668D",
            fg=THEME["white"]
        ).pack(side="left")

        btn_back = tk.Button(
            top_bar,
            text="← Back to CRUD Operations",
            command=lambda: self._navigate_to("hub"),
            bg="#028090",
            fg=THEME["white"],
            font=FONTS["caption_bold"],
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2"
        )
        btn_back.pack(side="right")

        # 2. Split Workspace
        workspace = tk.Frame(
            self,
            bg=THEME["gray_bg"],
            padx=20,
            pady=15
        )
        workspace.grid(row=1, column=0, sticky="nsew")
        workspace.columnconfigure(0, weight=3)
        workspace.columnconfigure(1, weight=2)
        workspace.rowconfigure(0, weight=1)

        # Left Column: Products Requiring Notifications
        left_card = tk.LabelFrame(
            workspace,
            text=" 1. Select Batch for Expiry Alert Dispatch ",
            font=FONTS["h3"],
            bg=THEME["white"],
            fg="#05668D",
            padx=12,
            pady=10
        )
        left_card.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 10)
        )
        left_card.columnconfigure(0, weight=1)
        left_card.rowconfigure(1, weight=1)

        # Filter bar
        filt_box = tk.Frame(left_card, bg=THEME["white"])
        filt_box.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 8)
        )

        tk.Label(
            filt_box,
            text="Filter Risk:",
            font=FONTS["body_bold"],
            bg=THEME["white"]
        ).pack(side="left", padx=(0, 5))

        self.combo_risk = ttk.Combobox(
            filt_box,
            state="readonly",
            values=[
                "All Alert Items",
                "EXPIRED Items Only",
                "Expiring ≤ 7 Days",
                "Expiring 8-30 Days"
            ],
            width=20
        )
        self.combo_risk.set("All Alert Items")
        self.combo_risk.pack(side="left")
        self.combo_risk.bind(
            "<<ComboboxSelected>>",
            lambda e: self.load_alerts()
        )

        # Alerts Table
        cols = (
            "id", "pid", "pname", "expiry",
            "days", "qty", "status", "sent"
        )

        self.tree = ttk.Treeview(
            left_card,
            columns=cols,
            show="headings",
            selectmode="browse"
        )

        self.tree.heading("id", text="Alert ID")
        self.tree.heading("pid", text="Product ID")
        self.tree.heading("pname", text="Product Name")
        self.tree.heading("expiry", text="Expiry Date")
        self.tree.heading("days", text="Days Left")
        self.tree.heading("qty", text="Stock Qty")
        self.tree.heading("status", text="Risk Status")
        self.tree.heading("sent", text="SMS Status")

        self.tree.column("id", width=70, anchor="center")
        self.tree.column("pid", width=75, anchor="center")
        self.tree.column("pname", width=170, anchor="w")
        self.tree.column("expiry", width=85, anchor="center")
        self.tree.column("days", width=70, anchor="center")
        self.tree.column("qty", width=65, anchor="center")
        self.tree.column("status", width=95, anchor="center")
        self.tree.column("sent", width=80, anchor="center")

        sb = ttk.Scrollbar(
            left_card,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(yscrollcommand=sb.set)
        self.tree.grid(row=1, column=0, sticky="nsew")
        sb.grid(row=1, column=1, sticky="ns")

        self.tree.bind(
            "<<TreeviewSelect>>",
            self._on_alert_selected
        )

        # Right Column: SMS Dispatch Composer
        right_card = tk.LabelFrame(
            workspace,
            text=" 2. SMS Alert Composer & Dispatch ",
            font=FONTS["h3"],
            bg=THEME["white"],
            fg="#05668D",
            padx=18,
            pady=15
        )
        right_card.grid(row=0, column=1, sticky="nsew")
        right_card.columnconfigure(1, weight=1)

        row = 0

        tk.Label(
            right_card,
            text="Target Batch:",
            font=FONTS["body_bold"],
            bg=THEME["white"]
        ).grid(row=row, column=0, sticky="w", pady=5)

        self.lbl_target = tk.Label(
            right_card,
            text="-- Please select from left --",
            font=FONTS["body_bold"],
            bg=THEME["white"],
            fg="#028090"
        )
        self.lbl_target.grid(
            row=row,
            column=1,
            sticky="w",
            pady=5
        )

        row += 1

        tk.Label(
            right_card,
            text="SMS Recipient:",
            font=FONTS["body_bold"],
            bg=THEME["white"]
        ).grid(row=row, column=0, sticky="w", pady=6)

        self.combo_recipient = ttk.Combobox(
            right_card,
            state="readonly",
            values=[
                "Store Department Manager (+1-555-0191)",
                "Supplier Logistics Coordinator (+1-555-0102)",
                "Discount Markdown Pricing Desk (+1-555-0188)",
                "Quality & Health Safety Inspector (+1-555-0177)"
            ],
            width=28
        )
        self.combo_recipient.current(0)
        self.combo_recipient.grid(
            row=row,
            column=1,
            sticky="ew",
            pady=6
        )
        self.combo_recipient.bind(
            "<<ComboboxSelected>>",
            lambda e: self._generate_sms_text()
        )

        row += 1

        tk.Label(
            right_card,
            text="Alert Directive:",
            font=FONTS["body_bold"],
            bg=THEME["white"]
        ).grid(row=row, column=0, sticky="w", pady=6)

        self.combo_type = ttk.Combobox(
            right_card,
            state="readonly",
            values=[
                "50% Clearance Markdown Notice",
                "Immediate Shelf Removal & Write-Off Order",
                "Supplier Return & Credit Note Request",
                "Routine Shelf Life Warning (Monitor)"
            ],
            width=28
        )
        self.combo_type.current(0)
        self.combo_type.grid(
            row=row,
            column=1,
            sticky="ew",
            pady=6
        )
        self.combo_type.bind(
            "<<ComboboxSelected>>",
            lambda e: self._generate_sms_text()
        )

        row += 1

        tk.Label(
            right_card,
            text="SMS Message Body:",
            font=FONTS["body_bold"],
            bg=THEME["white"]
        ).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(10, 4)
        )

        row += 1

        self.txt_sms = tk.Text(
            right_card,
            height=6,
            font=FONTS["body"],
            wrap="word",
            bg="#F4FAF9",
            bd=1,
            relief="solid"
        )
        self.txt_sms.grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="nsew",
            pady=(0, 6)
        )

        row += 1

        self.lbl_char_count = tk.Label(
            right_card,
            text="0 / 160 Characters",
            font=FONTS["caption"],
            bg=THEME["white"],
            fg=THEME["text_muted"]
        )
        self.lbl_char_count.grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w"
        )

        row += 1

        self.btn_send = tk.Button(
            right_card,
            text="📱 Dispatch SMS Alert Now",
            command=self._dispatch_sms,
            bg="#028090",
            fg=THEME["white"],
            font=FONTS["h3"],
            relief="flat",
            padx=15,
            pady=10,
            cursor="hand2",
            state="disabled"
        )
        self.btn_send.grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(15, 0)
        )

    def load_alerts(self):
        """Load expiry alerts and display them in the table."""

        for item in self.tree.get_children():
            self.tree.delete(item)

        df_alerts = self.storage.get_expiry_alerts()
        df_prod = self.storage.get_products()

        if df_alerts.empty:
            return

        # Fill product names using the products table when available.
        if "product_name" in df_alerts.columns and not df_alerts.empty:
            df = df_alerts.copy()

            if (
                not df_prod.empty
                and "product_name" in df_prod.columns
            ):
                name_map = dict(
                    zip(
                        df_prod["product_id"],
                        df_prod["product_name"]
                    )
                )

                df["product_name"] = (
                    df["product_name"]
                    .replace("", None)
                    .fillna(df["product_id"].map(name_map))
                    .fillna("Item")
                )
            else:
                df["product_name"] = (
                    df["product_name"].fillna("Item")
                )

        elif (
            not df_prod.empty
            and "product_id" in df_prod.columns
            and "product_name" in df_prod.columns
        ):
            df = df_alerts.merge(
                df_prod[["product_id", "product_name"]],
                on="product_id",
                how="left"
            )

            if "product_name" not in df.columns:
                df["product_name"] = "Item"

            df["product_name"] = df["product_name"].fillna("Item")

        else:
            df = df_alerts.copy()
            df["product_name"] = "Item"

        # Convert days until expiry into numeric values.
        df["days_num"] = pd.to_numeric(
            df["days_until_expiry"],
            errors="coerce"
        ).fillna(999).astype(int)

        # Apply risk filter.
        filt = self.combo_risk.get()

        if filt == "EXPIRED Items Only":
            df = df[df["alert_status"] == "EXPIRED"]

        elif filt == "Expiring ≤ 7 Days":
            df = df[df["alert_status"] == "EXPIRING_SOON_7"]

        elif filt == "Expiring 8-30 Days":
            df = df[df["alert_status"] == "EXPIRING_SOON_30"]

        df = df.sort_values(
            by="days_num",
            ascending=True
        )

        # Populate the table.
        for _, r in df.iterrows():
            self.tree.insert(
                "",
                "end",
                values=(
                    r.get("alert_id", ""),
                    r.get("product_id", ""),
                    r.get("product_name", "Item"),
                    r.get("expiry_date", ""),
                    f"{r['days_num']}d",
                    r.get("quantity_affected", 0),
                    r.get("alert_status", ""),
                    r.get("notification_sent", "")
                )
            )

    def _on_alert_selected(self, event=None):
        """Handle selection of an expiry alert."""

        sel = self.tree.selection()

        if not sel:
            return

        values = self.tree.item(sel[0], "values")

        self.selected_alert = {
            "alert_id": values[0],
            "product_id": values[1],
            "product_name": values[2],
            "expiry_date": values[3],
            "days": values[4],
            "qty": values[5],
            "status": values[6]
        }

        self.lbl_target.config(
            text=(
                f"{self.selected_alert['product_name']} "
                f"({self.selected_alert['product_id']})"
            )
        )

        self.btn_send.config(
            state="normal",
            bg="#028090"
        )

        self._generate_sms_text()

    def _generate_sms_text(self):
        """Generate the SMS body based on the selected alert."""

        if not self.selected_alert:
            return

        alert = self.selected_alert

        recipient = self.combo_recipient.get().split(" (")[0]
        directive = self.combo_type.get()

        msg = (
            f"[SUPERMARKET ALERT] Attention: {recipient}. "
            f"Product '{alert['product_name']}' "
            f"({alert['product_id']}) expires on "
            f"{alert['expiry_date']} ({alert['days']} left). "
            f"{alert['qty']} units on shelf. "
            f"Action Required: {directive}."
        )

        self.txt_sms.delete("1.0", tk.END)
        self.txt_sms.insert("1.0", msg)

        self.lbl_char_count.config(
            text=f"{len(msg)} Characters (Standard SMS)"
        )

    def _dispatch_sms(self):
        """Simulate SMS dispatch and update the alert notification status."""

        if not self.selected_alert:
            return

        aid = self.selected_alert["alert_id"]
        recipient = self.combo_recipient.get()
        msg_body = self.txt_sms.get("1.0", tk.END).strip()

        if not msg_body:
            return

        try:
            # Update alert notification status in storage.
            self.storage.update_alert_notification(
                aid,
                "Sent (SMS)"
            )
        except Exception as exc:
            logger.exception("Failed to update SMS notification status.")
            tk.messagebox.showerror(
                "SMS Dispatch Error",
                f"Could not update notification status:\n{exc}",
                parent=self
            )
            return

        # Display simulated delivery receipt.
        modal = tk.Toplevel(self)
        modal.title("SMS Dispatch Confirmation")
        modal.geometry("450x380")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        box = tk.Frame(
            modal,
            bg=THEME["white"],
            bd=2,
            relief="solid",
            padx=20,
            pady=20
        )
        box.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=15
        )

        tk.Label(
            box,
            text="📱 SMS DISPATCH RECEIPT",
            font=FONTS["h2"],
            bg=THEME["white"],
            fg="#05668D"
        ).pack()

        tk.Label(
            box,
            text="SIMULATED TELECOM GATEWAY",
            font=FONTS["caption_bold"],
            bg=THEME["white"],
            fg=THEME["success"]
        ).pack(pady=(0, 10))

        ttk.Separator(
            box,
            orient="horizontal"
        ).pack(fill="x", pady=5)

        details = [
            ("Gateway Status:", "200 OK - Simulated"),
            ("Recipient:", recipient),
            (
                "Dispatch Time:",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ),
            ("Alert ID:", aid),
            (
                "Batch Product:",
                self.selected_alert["product_name"]
            )
        ]

        for label, value in details:
            frame = tk.Frame(box, bg=THEME["white"])
            frame.pack(fill="x", pady=2)

            tk.Label(
                frame,
                text=label,
                font=FONTS["caption_bold"],
                bg=THEME["white"]
            ).pack(side="left")

            tk.Label(
                frame,
                text=value,
                font=FONTS["caption"],
                bg=THEME["white"],
                fg=THEME["text_secondary"]
            ).pack(side="right")

        ttk.Separator(
            box,
            orient="horizontal"
        ).pack(fill="x", pady=8)

        tk.Label(
            box,
            text="Message Body Transmitted:",
            font=FONTS["caption_bold"],
            bg=THEME["white"]
        ).pack(anchor="w")

        txt_prev = tk.Label(
            box,
            text=msg_body,
            font=FONTS["caption"],
            bg="#E0F7FA",
            fg="#05668D",
            wraplength=380,
            justify="left",
            padx=8,
            pady=6
        )
        txt_prev.pack(fill="x", pady=4)

        tk.Button(
            box,
            text="✓ Close Receipt",
            command=modal.destroy,
            font=FONTS["caption_bold"],
            bg="#00A896",
            fg=THEME["white"],
            relief="flat",
            padx=15,
            pady=5
        ).pack(pady=(10, 0))

        self.load_alerts()

    def _navigate_to(self, key):
        """Navigate to another application page."""

        if self.nav_callback:
            self.nav_callback(key)
