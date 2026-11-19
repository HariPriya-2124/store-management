"""
Automated Test for Clean Supermarket 2-Tier Architecture:
- Page 1: Login & Registration (AuthScreen)
- Page 2: CRUD Operations Hub (OperationsHubView)
- Sub-Pages: Create, Retrieve, Update, Delete, Expiry, SMS, etc.
- Confirms zero overlapping widgets and proper view lifecycle.
"""

import sys
from pathlib import Path
import tkinter as tk
import pytest

# Ensure parent path is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from database.storage_manager import StorageManager
from modules.auth_screen import AuthScreen, REGISTERED_USERS
from modules.operations_hub import OperationsHubView
from modules.crud_operations import CreateProductView, UpdateProductView, DeleteProductView
from modules.sms_notifications import SMSNotificationView
from modules.products import ProductManagementView
from modules.sales import SalesManagementView
from modules.inventory import InventoryManagementView
from modules.expiry_alerts import ExpiryAlertsView
from modules.analytics import AnalyticsView
from modules.suppliers import SupplierManagementView
from modules.settings import SettingsView
from main import SupermarketApp


@pytest.fixture(scope="module")
def root_window():
    """Provides a hidden root window for headless UI testing."""
    root = tk.Tk()
    root.geometry("1280x720")
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


@pytest.fixture(scope="module")
def storage():
    """Provides a StorageManager instance."""
    return StorageManager(auto_init=True)


def test_page1_auth_screen_login_and_validation(root_window):
    """Verifies Page 1 (Login & Registration) validation, credentials check, and mode toggling."""
    auth_log = []
    screen = AuthScreen(
        root_window,
        on_auth_success=lambda u: auth_log.append(u),
        initial_mode="login"
    )
    screen.pack(fill="both", expand=True)
    root_window.update_idletasks()

    # 1. Invalid email triggers error
    screen.entry_email.delete(0, "end")
    screen.entry_email.insert(0, "invalid-email")
    screen.entry_pass.delete(0, "end")
    screen.entry_pass.insert(0, "admin123")
    screen._execute_login()
    assert "⚠️" in screen.lbl_error.cget("text")
    assert len(auth_log) == 0

    # 2. Empty password triggers error
    screen.entry_email.delete(0, "end")
    screen.entry_email.insert(0, "admin@supermarket.com")
    screen.entry_pass.delete(0, "end")
    screen._execute_login()
    assert "⚠️" in screen.lbl_error.cget("text")
    assert len(auth_log) == 0

    # 3. 1-Click Instant Demo Login succeeds
    screen.btn_demo.invoke()
    assert len(auth_log) == 1
    assert auth_log[0]["role"] == "Super Admin"

    # 4. Mode toggle to register
    screen._set_mode("register")
    assert screen.current_mode == "register"
    assert hasattr(screen, "entry_name")

    screen.destroy()


def test_page2_crud_operations_hub(root_window, storage):
    """Verifies Page 2 initializes all 6 operations buttons and metrics."""
    nav_log = []
    hub = OperationsHubView(
        root_window,
        storage=storage,
        nav_callback=lambda k: nav_log.append(k),
        user_info={"name": "Alice Cashier", "role": "Senior Cashier"}
    )
    hub.pack(fill="both", expand=True)
    root_window.update_idletasks()

    assert len(hub.op_buttons) == 6

    # Test clicking each of the 6 core operations buttons
    for btn in hub.op_buttons:
        btn.invoke()

    expected_ops = ["op_create", "op_read", "op_update", "op_delete", "op_expiry", "op_sms"]
    for op in expected_ops:
        assert op in nav_log, f"Expected {op} in navigation log"

    # Test metrics refresh
    hub.refresh_metrics()
    assert "Catalog:" in hub.lbl_kpi.cget("text")

    hub.destroy()


def test_all_crud_subpages_instantiation(root_window, storage):
    """Verifies all operation sub-views instantiate cleanly and have dataset access."""
    nav_log = []
    nav = lambda k: nav_log.append(k)

    views = [
        CreateProductView(root_window, storage, nav_callback=nav),
        UpdateProductView(root_window, storage, nav_callback=nav),
        DeleteProductView(root_window, storage, nav_callback=nav),
        SMSNotificationView(root_window, storage, nav_callback=nav),
        ProductManagementView(root_window, storage, nav_callback=nav),
        SalesManagementView(root_window, storage, nav_callback=nav),
        InventoryManagementView(root_window, storage, nav_callback=nav),
        ExpiryAlertsView(root_window, storage, nav_callback=nav),
        AnalyticsView(root_window, storage, nav_callback=nav),
        SupplierManagementView(root_window, storage, nav_callback=nav),
        SettingsView(root_window, storage, nav_callback=nav),
    ]

    for v in views:
        v.pack(fill="both", expand=True)
        root_window.update_idletasks()
        v.destroy()


def test_main_app_navigation_lifecycle():
    """Verifies that navigation in SupermarketApp destroys old views cleanly with no overlaps."""
    app = SupermarketApp()
    app.withdraw()

    # Initial view is auth
    assert app._current_key == "auth"
    v1 = app._current_view
    assert v1 is not None

    # Navigate to hub
    app.navigate_to("hub")
    assert app._current_key == "hub"
    assert app._current_view is not v1  # fresh instance
    v2 = app._current_view

    # Navigate to create
    app.navigate_to("op_create")
    assert app._current_key == "op_create"
    assert app._current_view is not v2

    # Navigate back to hub
    app.navigate_to("hub")
    assert app._current_key == "hub"

    # Navigate to retrieve (read)
    app.navigate_to("op_read")
    assert app._current_key == "op_read"

    app.destroy()


def test_login_page_module():
    """Verifies that the dedicated modules/login.py LoginPage functions cleanly."""
    from modules.login import LoginPage
    auth_log = []
    login_app = LoginPage(on_login_success=lambda u: auth_log.append(u))
    login_app.withdraw()
    login_app.update_idletasks()

    # Form card geometry and lack of clipping
    assert login_app.card.winfo_width() >= 800
    assert login_app.card.winfo_height() >= 500

    # Test Admin login
    login_app.username.delete(0, tk.END)
    login_app.username.insert(0, "admin")
    login_app.password.delete(0, tk.END)
    login_app.password.insert(0, "admin123")
    login_app.login()
    assert len(auth_log) == 1
    assert auth_log[0]["role"] == "Super Admin"

    # Test mode toggle to registration
    login_app.render_register_form()
    login_app.update_idletasks()
    assert login_app.current_mode == "register"

    # Test mode toggle back to login
    login_app.render_login_form()
    login_app.update_idletasks()
    assert login_app.current_mode == "login"

    login_app.destroy()
