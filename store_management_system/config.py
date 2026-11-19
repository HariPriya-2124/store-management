
"""
Configuration Module for Store Management System.
Handles paths, constants, themes, and runtime environment settings.
Compatible with standard Python execution and PyInstaller bundled binaries.
"""

import os
import sys
import tempfile
from pathlib import Path


# Fix Matplotlib cache directory and Tkinter deprecation warnings
os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path(tempfile.gettempdir()) / "store_management_mpl")
)
os.environ.setdefault("TK_SILENCE_DEPRECATION", "1")


# Determine application execution mode and base directories
IS_FROZEN = getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")

if IS_FROZEN:
    # Running inside a PyInstaller bundle
    BUNDLE_DIR = Path(sys._MEIPASS)

    custom_dir = os.environ.get("STORE_DATA_DIR")

    if custom_dir:
        USER_DATA_DIR = Path(custom_dir)
    else:
        # Writable user application data directory with automatic fallback
        try:
            if sys.platform == "win32":
                app_data_root = Path(
                    os.environ.get(
                        "LOCALAPPDATA",
                        Path.home() / "AppData" / "Local"
                    )
                )
            elif sys.platform == "darwin":
                app_data_root = (
                    Path.home()
                    / "Library"
                    / "Application Support"
                )
            else:
                app_data_root = Path(
                    os.environ.get(
                        "XDG_DATA_HOME",
                        Path.home() / ".local" / "share"
                    )
                )

            target_dir = app_data_root / "StoreManagementSystem"
            target_dir.mkdir(parents=True, exist_ok=True)
            USER_DATA_DIR = target_dir

        except (PermissionError, FileNotFoundError, OSError):
            USER_DATA_DIR = (
                Path(sys.executable).resolve().parent / "store_data"
            )

else:
    # Running from source
    BUNDLE_DIR = Path(__file__).resolve().parent

    custom_dir = os.environ.get("STORE_DATA_DIR")

    if custom_dir:
        USER_DATA_DIR = Path(custom_dir)
    else:
        USER_DATA_DIR = BUNDLE_DIR


# Establish working directories
DATA_DIR = USER_DATA_DIR / "data"
LOGS_DIR = USER_DATA_DIR / "logs"
BACKUPS_DIR = USER_DATA_DIR / "backups"

ASSETS_DIR = BUNDLE_DIR / "assets"

STOREFRONT_IMG_PATH = (
    ASSETS_DIR / "front.png"
    if (ASSETS_DIR / "front.png").exists()
    else ASSETS_DIR / "supermarket_front.png"
)

SHOPPERS_IMG_PATH = (
    ASSETS_DIR / "shoppers.png"
    if (ASSETS_DIR / "shoppers.png").exists()
    else ASSETS_DIR / "supermarket_shoppers.png"
)

AISLE_HUB_IMG_PATH = (
    ASSETS_DIR / "supermarket_bg.jpg"
    if (ASSETS_DIR / "supermarket_bg.jpg").exists()
    else (
        ASSETS_DIR / "supermarket_aisle_photoreal.png"
        if (ASSETS_DIR / "supermarket_aisle_photoreal.png").exists()
        else (
            ASSETS_DIR / "hub.png"
            if (ASSETS_DIR / "hub.png").exists()
            else ASSETS_DIR / "supermarket_aisle_hub.png"
        )
    )
)

SUPERMARKET_IMG_PATH = (
    ASSETS_DIR / "supermarket.png"
    if (ASSETS_DIR / "supermarket.png").exists()
    else STOREFRONT_IMG_PATH
)


# Ensure runtime directories exist safely
for directory in [DATA_DIR, LOGS_DIR, BACKUPS_DIR]:
    try:
        directory.mkdir(parents=True, exist_ok=True)

    except (PermissionError, FileNotFoundError, OSError):
        # Fallback to current working directory if system directory is blocked
        alt_dir = Path.cwd() / "store_runtime_data" / directory.name
        alt_dir.mkdir(parents=True, exist_ok=True)

        if directory == DATA_DIR:
            DATA_DIR = alt_dir
        elif directory == LOGS_DIR:
            LOGS_DIR = alt_dir
        elif directory == BACKUPS_DIR:
            BACKUPS_DIR = alt_dir


try:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    pass


# ---------------------------------------------------------
# Dataset file paths
# ---------------------------------------------------------

CUSTOMERS_FILE = DATA_DIR / "customers.csv"
PRODUCTS_FILE = DATA_DIR / "products.csv"
SUPPLIERS_FILE = DATA_DIR / "suppliers.csv"
SALES_FILE = DATA_DIR / "sales.csv"
STOCK_MOVEMENTS_FILE = DATA_DIR / "stock_movements.csv"
EXPIRY_ALERTS_FILE = DATA_DIR / "expiry_alerts.csv"
DB_PATH = DATA_DIR / "store_management.db"

HUB_IMG_PATH = AISLE_HUB_IMG_PATH
FRONT_IMG_PATH = STOREFRONT_IMG_PATH
SUPERMARKET_BG_PATH = ASSETS_DIR / "supermarket_bg.jpg"

LOG_FILE = LOGS_DIR / "store_app.log"


# ---------------------------------------------------------
# Application Metadata
# ---------------------------------------------------------

APP_NAME = "Store Management System"
APP_SUBTITLE = "Python for Data Science | Enterprise POS & Inventory"
APP_VERSION = "1.0.0"
CURRENCY_SYMBOL = "₹"
CURRENCY_CODE = "INR"


# ---------------------------------------------------------
# Supermarket Theme Color Palette
# Turquoise, Sky Blue, White & Soft Green
# ---------------------------------------------------------

THEME = {
    # Primary Supermarket Brand Palette
    "turquoise": "#028090",
    "turquoise_accent": "#00A896",
    "turquoise_dark": "#05668D",
    "sky_blue": "#00B4D8",
    "sky_blue_light": "#E0F7FA",
    "sky_blue_soft": "#CAF0F8",
    "soft_green": "#52B788",
    "soft_green_light": "#D8F3DC",
    "soft_green_dark": "#2D6A4F",
    "coral_accent": "#E63946",
    "warm_wood": "#D4A373",
    "warm_wood_dark": "#C58940",

    # Core UI Standards
    "navy_primary": "#05668D",
    "navy_dark": "#0A192F",
    "navy_header": "#028090",
    "navy_sidebar": "#05668D",
    "navy_accent": "#00A896",
    "blue_light": "#E0F7FA",
    "blue_soft": "#CAF0F8",
    "white": "#FFFFFF",
    "gray_bg": "#F4FAF9",
    "gray_card": "#FFFFFF",
    "gray_border": "#BEE3DB",
    "gray_hover": "#E0F7FA",
    "gray_alt_row": "#F7FCFC",

    # Text Colors
    "text_primary": "#1D3557",
    "text_secondary": "#2B475D",
    "text_muted": "#5C768D",
    "text_inverted": "#FFFFFF",
    "text_brand": "#028090",

    # Status Indicators
    "success": "#2D6A4F",
    "success_bg": "#D8F3DC",
    "warning": "#E76F51",
    "warning_bg": "#FFE8D6",
    "danger": "#E63946",
    "danger_bg": "#FFE5E7",
    "info": "#0077B6",
    "info_bg": "#E0F7FA",
}


# ---------------------------------------------------------
# Typography Configurations
# ---------------------------------------------------------

FONT_FAMILY = (
    "Segoe UI"
    if sys.platform == "win32"
    else (
        "SF Pro Text"
        if sys.platform == "darwin"
        else "Helvetica"
    )
)

FONTS = {
    "h1": (FONT_FAMILY, 16, "bold"),
    "h2": (FONT_FAMILY, 13, "bold"),
    "h3": (FONT_FAMILY, 11, "bold"),
    "body": (FONT_FAMILY, 10),
    "body_bold": (FONT_FAMILY, 10, "bold"),
    "caption": (FONT_FAMILY, 9),
    "caption_bold": (FONT_FAMILY, 9, "bold"),
    "card_title": (FONT_FAMILY, 10, "bold"),
    "card_value": (FONT_FAMILY, 18, "bold"),
    "card_sub": (FONT_FAMILY, 8),
    "sidebar": (FONT_FAMILY, 11),
    "sidebar_bold": (FONT_FAMILY, 11, "bold"),
}


# ---------------------------------------------------------
# Expiry Notification Thresholds (Days)
# ---------------------------------------------------------

EXPIRY_CRITICAL_DAYS = 0
EXPIRY_WARNING_DAYS = 7
EXPIRY_CAUTION_DAYS = 30


# ---------------------------------------------------------
# Inventory Stock Thresholds
# ---------------------------------------------------------

DEFAULT_MINIMUM_STOCK = 15
CRITICAL_STOCK_THRESHOLD = 5
