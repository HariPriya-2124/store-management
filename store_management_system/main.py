"""
Main Application Launcher for Store Management System.
Implements the 2-Tier Supermarket-Themed Architecture:

  PAGE 1 ─ Login & Registration Page (AuthScreen)
  PAGE 2 ─ Main CRUD Operations Hub (OperationsHubView)
  SUB-PAGES ─ Dedicated CRUD Operations & Management Views:
      • Create Operation   (CreateProductView)
      • Retrieve Operation (ProductManagementView)
      • Update Operation   (UpdateProductView)
      • Delete Operation   (DeleteProductView)
      • Expiry Date        (ExpiryAlertsView)
      • Send SMS           (SMSNotificationView)
      • POS Sales          (SalesManagementView)
      • Inventory Ledger   (InventoryManagementView)
      • Data Analytics     (AnalyticsView)
      • Suppliers          (SupplierManagementView)
      • Settings & Backups (SettingsView)

View lifecycle guarantees:
  Every navigation completely destroys the previous view before
  instantiating the new view, guaranteeing ZERO overlapping widgets.
"""

import os
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

# Path bootstrapping
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from config import APP_NAME, APP_SUBTITLE, APP_VERSION, FONTS, THEME
from database.storage_manager import StorageManager

# Screens & Views
from modules.auth_screen import AuthScreen
from modules.operations_hub import OperationsHubView
from modules.crud_operations import CreateProductView, UpdateProductView, DeleteProductView
from modules.sms_notifications import SMSNotificationView
from modules.products import ProductManagementView
from modules.suppliers import SupplierManagementView
from modules.sales import SalesManagementView
from modules.inventory import InventoryManagementView
from modules.expiry_alerts import ExpiryAlertsView
from modules.analytics import AnalyticsView
from modules.settings import SettingsView

from utils.logger import get_logger

logger = get_logger("MainApp")


class SupermarketApp(tk.Tk):
    """
    Root Desktop Window for Store Management System.
    """

    def __init__(self):
        super().__init__()

        self.title(f"{APP_NAME} – {APP_SUBTITLE} (v{APP_VERSION})")
        self.geometry("1300x840")
        self.minsize(1050, 680)
        self.configure(bg="#E0F7FA")

        # Backend storage (CSV datasets)
        self.storage = StorageManager(auto_init=True)

        # Active user credentials populated after login
        self._user_info = {}

        # Single active view tracker
        self._current_view = None
        self._current_key = None

        # Container frame
        self._container = tk.Frame(self, bg="#E0F7FA")
        self._container.pack(fill="both", expand=True)

        self._configure_styles()

        # Bring window to foreground safely without Cocoa topmost glitch
        try:
            self.lift()
            self.focus_force()
        except Exception:
            pass

        # Start on Hub if authenticated from login module, else Page 1
        auth_user = os.environ.get("STORE_AUTH_USER")
        if auth_user:
            self._user_info = {
                "name": auth_user.capitalize(),
                "role": "Super Admin" if "admin" in auth_user.lower() else "Senior Cashier",
                "email": f"{auth_user}@supermarket.com"
            }
            self.navigate_to("hub")
        else:
            self.navigate_to("auth")

        self.update_idletasks()

    def _configure_styles(self):
        """Configures ttk widget styles for supermarket theme."""
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        teal        = THEME.get("turquoise_dark",   "#05668D")
        teal_accent = THEME.get("turquoise",         "#028090")
        sky         = THEME.get("sky_blue",          "#00B4D8")
        white       = THEME.get("white",             "#FFFFFF")
        gray_bg     = THEME.get("gray_bg",           "#F4F6F9")
        txt_pri     = THEME.get("text_primary",      "#1A1A2E")
        txt_sec     = THEME.get("text_secondary",    "#4A5568")

        # Notebook
        style.configure("TNotebook", background=gray_bg, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            font=FONTS["body_bold"], padding=[14, 6],
            background=white, foreground=txt_sec,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", teal_accent)],
            foreground=[("selected", white)],
        )

        # Treeview
        style.configure(
            "Treeview",
            background=white, foreground=txt_pri,
            rowheight=26, fieldbackground=white,
            font=FONTS["body"], borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            font=FONTS["caption_bold"],
            background=teal,
            foreground=white,
            relief="flat", padding=[6, 5],
        )
        style.map(
            "Treeview.Heading",
            background=[("active", teal_accent)],
        )
        style.map(
            "Treeview",
            background=[("selected", sky)],
            foreground=[("selected", txt_pri)],
        )

        # Controls
        style.configure("TButton", font=FONTS["body"])
        style.configure("TCombobox", font=FONTS["body"])
        style.configure("TScrollbar", troughcolor=gray_bg)

    def _sync_all_views(self):
        """Signals that datasets changed (e.g. sale made, inventory moved)."""
        logger.info("Datasets synchronized across modules.")

    def navigate_to(self, key: str):
        """
        Transitions to a target view.
        Crucial: Completely destroys the current view first to eliminate
        any chance of overlapping widgets or ghost elements.
        """
        # Aliases
        if key in ("home", "login", "register", "logout"):
            if key == "logout":
                self._user_info = {}
            key = "auth"

        # Destroy existing view completely
        if self._current_view is not None:
            try:
                self._current_view.destroy()
            except Exception as e:
                logger.warning(f"Error destroying view: {e}")
            self._current_view = None

        # Ensure container has no residual widgets
        for child in self._container.winfo_children():
            try:
                child.destroy()
            except Exception:
                pass

        # Build fresh target view
        target = self._build_view(key)
        if target is None:
            logger.error(f"Cannot build view for key: '{key}'")
            return

        # Pack target cleanly to fill container
        target.pack(fill="both", expand=True)
        self._current_view = target
        self._current_key = key
        self.update_idletasks()

        # Window title based on active view
        titles = {
            "auth": "Page 1: Login & Registration",
            "hub": "Page 2: Main CRUD Operations Hub",
            "op_create": "Sub-Page: Create Product",
            "op_read": "Sub-Page: Retrieve Products",
            "op_update": "Sub-Page: Update Product",
            "op_delete": "Sub-Page: Delete Product",
            "op_expiry": "Sub-Page: Expiry Date Management",
            "op_sms": "Sub-Page: Send SMS Notifications",
            "sales": "Sub-Page: POS Sales & Transactions",
            "inventory": "Sub-Page: Inventory Stock Movements",
            "analytics": "Sub-Page: Data Science & Analytics",
            "suppliers": "Sub-Page: Supplier Management",
            "settings": "Sub-Page: Database Backups & Settings",
        }
        sub_title = titles.get(key, "Store Management")
        self.title(f"{APP_NAME} – {sub_title}")

    def _build_view(self, key: str) -> tk.Widget:
        """Instantiates and returns the requested view with datasets wired."""
        c = self._container
        nav = self.navigate_to

        # ── PAGE 1: Login & Registration ─────────────────────────────────────
        if key == "auth":
            return AuthScreen(
                c,
                on_auth_success=self._on_auth_success,
                initial_mode="login"
            )

        # ── PAGE 2: Main CRUD Operations Hub ─────────────────────────────────
        if key == "hub":
            return OperationsHubView(
                c,
                storage=self.storage,
                nav_callback=nav,
                user_info=self._user_info
            )

        # ── SUB-PAGE 1: CREATE OPERATION ─────────────────────────────────────
        if key == "op_create":
            return CreateProductView(c, storage=self.storage, nav_callback=nav)

        # ── SUB-PAGE 2: RETRIEVE OPERATION ───────────────────────────────────
        if key == "op_read":
            return ProductManagementView(c, storage=self.storage, nav_callback=nav)

        # ── SUB-PAGE 3: UPDATE OPERATION ─────────────────────────────────────
        if key == "op_update":
            return UpdateProductView(c, storage=self.storage, nav_callback=nav)

        # ── SUB-PAGE 4: DELETE OPERATION ─────────────────────────────────────
        if key == "op_delete":
            return DeleteProductView(c, storage=self.storage, nav_callback=nav)

        # ── SUB-PAGE 5: EXPIRY DATE OPERATION ────────────────────────────────
        if key == "op_expiry":
            return ExpiryAlertsView(
                c,
                storage=self.storage,
                on_disposal_completed=self._sync_all_views,
                nav_callback=nav
            )

        # ── SUB-PAGE 6: SEND SMS NOTIFICATION ────────────────────────────────
        if key == "op_sms":
            return SMSNotificationView(c, storage=self.storage, nav_callback=nav)

        # ── EXTENDED SUB-PAGES ───────────────────────────────────────────────
        if key == "sales":
            return SalesManagementView(
                c,
                storage=self.storage,
                on_sale_completed=self._sync_all_views,
                nav_callback=nav
            )

        if key == "inventory":
            return InventoryManagementView(
                c,
                storage=self.storage,
                on_inventory_changed=self._sync_all_views,
                nav_callback=nav
            )

        if key == "analytics":
            return AnalyticsView(c, storage=self.storage, nav_callback=nav)

        if key == "suppliers":
            return SupplierManagementView(c, storage=self.storage, nav_callback=nav)

        if key == "settings":
            return SettingsView(
                c,
                storage=self.storage,
                on_data_restored=self._sync_all_views,
                nav_callback=nav
            )

        # Fallback to hub
        logger.warning(f"Unknown navigation view '{key}', falling back to hub.")
        return OperationsHubView(c, storage=self.storage, nav_callback=nav, user_info=self._user_info)

    def _on_auth_success(self, user_info: dict):
        """Called when user successfully logs in or registers."""
        self._user_info = user_info
        logger.info(f"User logged in: {user_info.get('name')} ({user_info.get('role')})")
        # Navigate directly to Page 2: CRUD Operations Hub
        self.navigate_to("hub")


def main():
    """Application entry point."""
    logger.info("Starting Store Management System Application...")
    app = SupermarketApp()
    app.update_idletasks()
    try:
        app.mainloop()
    except Exception as exc:
        logger.critical(f"Unhandled exception in mainloop: {exc}", exc_info=True)
        messagebox.showerror("Fatal Error", f"An unexpected error occurred:\n{exc}")


if __name__ == "__main__":
    main()
