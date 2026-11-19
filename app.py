"""
Store Management System – Streamlit Application
Enterprise Point-of-Sale, Inventory Tracking, Expiry Management & Data Science.
Crafted with modern typography, glassmorphism, responsive cards & supermarket palette.
"""

import sys
from pathlib import Path
import streamlit as st

# Setup sys.path
BASE_DIR = Path(__file__).resolve().parent
SMS_DIR = BASE_DIR / "store_management_system"
if str(SMS_DIR) not in sys.path:
    sys.path.insert(0, str(SMS_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from database.storage_manager import StorageManager
from streamlit_ui.ui_helpers import render_html
from streamlit_ui.auth_view import render_auth_view
from streamlit_ui.hub_view import render_hub_view
from streamlit_ui.crud_views import (
    render_create_view,
    render_retrieve_view,
    render_update_view,
    render_delete_view,
    render_expiry_view,
    render_sms_view,
)
from streamlit_ui.modules_views import (
    render_sales_view,
    render_inventory_view,
    render_analytics_view,
    render_suppliers_view,
    render_settings_view,
)

# -----------------------------------------------------------------------------
# 1. PAGE CONFIG & LUXURY DESIGN SYSTEM
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Store Management System | Enterprise Suite",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject Global Aesthetic CSS Design System
render_html(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@500;600;700;800&display=swap');

    :root {
        --primary: #028090;
        --primary-dark: #05668D;
        --secondary: #00B4D8;
        --accent-emerald: #10B981;
        --accent-rose: #E63946;
        --accent-amber: #F59E0B;
        --navy-dark: #0A192F;
        --slate-bg: #F8FAFC;
        --card-border: #E2E8F0;
        --font-main: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        --font-heading: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    html, body {
        font-family: var(--font-main) !important;
        color: #1E293B;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: var(--font-heading) !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
        color: #0F172A;
    }

    /* Background smoothness */
    .stApp {
        background-color: #F8FAFC !important;
        color: #0F172A;
    }

    /* High-contrast widget labels */
    div[data-testid="stWidgetLabel"] label, 
    div[data-testid="stWidgetLabel"] p,
    label[data-testid="stWidgetLabel"] {
        font-size: 0.92rem !important;
        font-weight: 700 !important;
        color: #0F172A !important;
        margin-bottom: 4px !important;
    }

    /* High contrast input styling */
    input[type="text"], input[type="password"], input[type="number"], div[data-baseweb="input"] input {
        background-color: #F8FAFC !important;
        color: #0F172A !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 8px !important;
    }
    input[type="text"]:focus, input[type="password"]:focus, input[type="number"]:focus, div[data-baseweb="input"] input:focus {
        background-color: #FFFFFF !important;
        border-color: #028090 !important;
        box-shadow: 0 0 0 3px rgba(2, 128, 144, 0.15) !important;
    }

    /* Metric Cards Glassmorphism */
    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        padding: 1.1rem 1.4rem;
        border-radius: 14px;
        box-shadow: 0 4px 15px -3px rgba(0, 0, 0, 0.04), 0 2px 6px -2px rgba(0, 0, 0, 0.02);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
        position: relative;
        overflow: hidden;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 25px -5px rgba(2, 128, 144, 0.12), 0 4px 10px -2px rgba(0, 0, 0, 0.04);
        border-color: #CBD5E1;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.04em !important;
        color: #64748B !important;
    }
    div[data-testid="stMetricValue"] {
        font-family: var(--font-heading) !important;
        font-size: 1.85rem !important;
        font-weight: 700 !important;
        color: #05668D !important;
        letter-spacing: -0.03em !important;
    }

    /* Primary Buttons */
    button[kind="primary"] {
        background: linear-gradient(135deg, #028090, #00B4D8) !important;
        border: none !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        padding: 0.6rem 1.4rem !important;
        box-shadow: 0 4px 12px rgba(2, 128, 144, 0.25) !important;
        transition: all 0.25s ease !important;
    }
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #05668D, #028090) !important;
        box-shadow: 0 6px 18px rgba(2, 128, 144, 0.35) !important;
        transform: translateY(-2px) !important;
    }

    /* Secondary Buttons */
    button[kind="secondary"] {
        border-radius: 10px !important;
        font-weight: 600 !important;
        border: 1px solid #CBD5E1 !important;
        background: #FFFFFF !important;
        color: #334155 !important;
        transition: all 0.2s ease !important;
    }
    button[kind="secondary"]:hover {
        border-color: #028090 !important;
        color: #028090 !important;
        background: #F0FDF4 !important;
    }

    /* Form Containers */
    div[data-testid="stForm"] {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 1.8rem;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.04);
    }

    /* Container Borders with Hover Elevation */
    div[data-testid="stVerticalBlock"] > div[data-testid="stContainer"] {
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        border-radius: 14px;
    }
    div[data-testid="stVerticalBlock"] > div[data-testid="stContainer"]:hover {
        border-color: #00B4D8 !important;
        box-shadow: 0 10px 25px -4px rgba(0, 180, 216, 0.12);
    }

    /* Custom Modern Tabs */
    button[data-baseweb="tab"] {
        font-family: var(--font-heading) !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.4rem !important;
        white-space: nowrap !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #028090 !important;
        border-bottom-color: #028090 !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0A192F 0%, #0F172A 100%) !important;
        color: #F8FAFC !important;
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] p {
        color: #F8FAFC !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div {
        gap: 4px;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label {
        background: rgba(255, 255, 255, 0.04);
        border-radius: 8px;
        padding: 0.4rem 0.8rem;
        margin-bottom: 2px;
        transition: all 0.2s ease;
        border-left: 3px solid transparent;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {
        background: rgba(2, 128, 144, 0.2);
        border-left: 3px solid #00B4D8;
    }
    </style>
    """
)


# -----------------------------------------------------------------------------
# 2. STORAGE SINGLETON & SESSION STATE
# -----------------------------------------------------------------------------
@st.cache_resource
def get_storage():
    return StorageManager(auto_init=True)

storage = get_storage()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_info" not in st.session_state:
    st.session_state.user_info = {}
if "current_page" not in st.session_state:
    st.session_state.current_page = "auth"


# -----------------------------------------------------------------------------
# 3. SIDEBAR NAVIGATION
# -----------------------------------------------------------------------------
with st.sidebar:
    render_html(
        """
        <div style="display: flex; align-items: center; gap: 10px; padding: 0.5rem 0 1rem 0;">
            <div style="background: #028090; width: 38px; height: 38px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1.25rem;">
                🛒
            </div>
            <div>
                <div style="font-family: 'Outfit', sans-serif; font-size: 1.15rem; font-weight: 700; color: #FFFFFF;">
                    StorePRO
                </div>
                <div style="font-size: 0.75rem; color: #94A3B8;">Retail Management</div>
            </div>
        </div>
        """
    )

    if st.session_state.authenticated:
        user = st.session_state.user_info
        role_color = "#10B981" if "admin" in user.get("role", "").lower() else "#00B4D8"
        render_html(
            f"""
            <div style="background: rgba(255, 255, 255, 0.06); border-radius: 10px; padding: 0.75rem 0.9rem; margin-bottom: 1rem;">
                <div style="font-weight: 600; color: #FFFFFF; font-size: 0.9rem;">{user.get('name', 'Staff')}</div>
                <div style="font-size: 0.75rem; color: {role_color}; font-weight: 500;">{user.get('role', 'Member')}</div>
                <div style="font-size: 0.72rem; color: #94A3B8; margin-top: 2px;">{user.get('email', '')}</div>
            </div>
            """
        )

        nav_options = {
            "Dashboard": "hub",
            "Products": "op_read",
            "Add Product": "op_create",
            "Edit Product": "op_update",
            "Delete Product": "op_delete",
            "Point of Sale": "sales",
            "Stock Movements": "inventory",
            "Expiry Tracking": "op_expiry",
            "SMS Alerts": "op_sms",
            "Analytics": "analytics",
            "Suppliers": "suppliers",
            "Settings & Backups": "settings",
        }

        current_label = next((k for k, v in nav_options.items() if v == st.session_state.current_page), "Dashboard")

        selected_label = st.radio(
            "Navigation",
            list(nav_options.keys()),
            index=list(nav_options.keys()).index(current_label) if current_label in nav_options else 0,
        )
        target_page = nav_options[selected_label]

        if target_page != st.session_state.current_page:
            st.session_state.current_page = target_page
            st.rerun()

        render_html("<div style='height: 15px;'></div>")
        if st.button("Sign Out", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_info = {}
            st.session_state.current_page = "auth"
            st.rerun()
    else:
        render_html(
            """
            <div style="color: #94A3B8; font-size: 0.85rem; padding: 0.5rem 0;">
                Please sign in to access the system.
            </div>
            """
        )


# -----------------------------------------------------------------------------
# 4. ROUTER DISPATCH
# -----------------------------------------------------------------------------
page = st.session_state.current_page

if not st.session_state.authenticated or page == "auth":
    render_auth_view()
elif page == "hub":
    render_hub_view(storage)
elif page == "op_create":
    render_create_view(storage)
elif page == "op_read":
    render_retrieve_view(storage)
elif page == "op_update":
    render_update_view(storage)
elif page == "op_delete":
    render_delete_view(storage)
elif page == "op_expiry":
    render_expiry_view(storage)
elif page == "op_sms":
    render_sms_view(storage)
elif page == "sales":
    render_sales_view(storage)
elif page == "inventory":
    render_inventory_view(storage)
elif page == "analytics":
    render_analytics_view(storage)
elif page == "suppliers":
    render_suppliers_view(storage)
elif page == "settings":
    render_settings_view(storage)
else:
    render_hub_view(storage)
