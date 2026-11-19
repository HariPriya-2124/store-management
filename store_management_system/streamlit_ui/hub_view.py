"""
Dashboard View for Store Management System.
Clean, executive overview with operational metrics and quick navigation.
"""

from datetime import datetime
import streamlit as st
import pandas as pd
from utils.helpers import format_currency
from streamlit_ui.ui_helpers import render_html


def render_hub_view(storage):
    """Renders the clean, modern operational dashboard."""
    user = st.session_state.get("user_info", {})
    user_name = user.get("name", "Administrator")

    # Header
    render_html(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid #E2E8F0;">
            <div>
                <h2 style="margin: 0; font-size: 1.75rem; font-weight: 700; color: #0F172A;">Dashboard</h2>
                <p style="margin: 4px 0 0 0; color: #64748B; font-size: 0.95rem;">Welcome back, {user_name}</p>
            </div>
            <div style="font-size: 0.85rem; color: #64748B;">
                {datetime.now().strftime("%A, %d %B %Y")}
            </div>
        </div>
        """
    )

    # Key Performance Indicators
    try:
        df_prod = storage.get_products()
        df_sales = storage.get_sales()
        df_exp = storage.get_expiry_alerts()

        prod_count = len(df_prod) if not df_prod.empty else 0
        total_units = int(pd.to_numeric(df_prod["stock_quantity"], errors="coerce").fillna(0).sum()) if not df_prod.empty else 0
        sales_count = len(df_sales) if not df_sales.empty else 0
        exp_count = len(df_exp) if not df_exp.empty else 0

        tot_rev = 0.0
        if not df_sales.empty and "total_amount" in df_sales.columns:
            tot_rev = float(pd.to_numeric(df_sales["total_amount"], errors="coerce").fillna(0.0).sum())

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Catalog Products", f"{prod_count:,}", f"{total_units:,} units total")
        k2.metric("Orders Completed", f"{sales_count:,}")
        k3.metric("Total Revenue", format_currency(tot_rev))
        k4.metric("Expiry Alerts", f"{exp_count:,}", f"{exp_count} flag(s)" if exp_count > 0 else None, delta_color="inverse")
    except Exception as e:
        st.warning(f"Unable to load summary metrics: {e}")

    render_html("<div style='height: 15px;'></div>")
    st.markdown("### Quick Actions")

    # 6 Clean Quick Navigation Cards
    r1_c1, r1_c2, r1_c3 = st.columns(3)

    with r1_c1:
        with st.container(border=True):
            st.markdown("#### Products")
            st.caption("Search, filter, and export the complete product catalog.")
            if st.button("View Catalog", key="hub_view_prod", use_container_width=True, type="primary"):
                st.session_state.current_page = "op_read"
                st.rerun()

    with r1_c2:
        with st.container(border=True):
            st.markdown("#### Add Product")
            st.caption("Register new merchandise with pricing and stock quantities.")
            if st.button("New Product", key="hub_add_prod", use_container_width=True):
                st.session_state.current_page = "op_create"
                st.rerun()

    with r1_c3:
        with st.container(border=True):
            st.markdown("#### Point of Sale")
            st.caption("Open the checkout terminal for fast customer billing.")
            if st.button("Open POS", key="hub_open_pos", use_container_width=True):
                st.session_state.current_page = "sales"
                st.rerun()

    r2_c1, r2_c2, r2_c3 = st.columns(3)

    with r2_c1:
        with st.container(border=True):
            st.markdown("#### Expiry Tracking")
            st.caption("Monitor batches approaching expiration and manage disposal.")
            if st.button("Check Expiry", key="hub_check_exp", use_container_width=True):
                st.session_state.current_page = "op_expiry"
                st.rerun()

    with r2_c2:
        with st.container(border=True):
            st.markdown("#### Inventory Ledger")
            st.caption("Review stock receiving, damage write-offs, and audit trails.")
            if st.button("Stock Movements", key="hub_inv_mov", use_container_width=True):
                st.session_state.current_page = "inventory"
                st.rerun()

    with r2_c3:
        with st.container(border=True):
            st.markdown("#### Analytics")
            st.caption("View revenue reports, category breakdowns, and performance.")
            if st.button("View Reports", key="hub_analytics", use_container_width=True):
                st.session_state.current_page = "analytics"
                st.rerun()

    render_html("<div style='height: 10px;'></div>")
    st.markdown("### Other Modules")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        if st.button("Edit Product", use_container_width=True, key="hub_edit_prod"):
            st.session_state.current_page = "op_update"
            st.rerun()
    with m2:
        if st.button("Suppliers", use_container_width=True, key="hub_suppliers"):
            st.session_state.current_page = "suppliers"
            st.rerun()
    with m3:
        if st.button("SMS Alerts", use_container_width=True, key="hub_sms"):
            st.session_state.current_page = "op_sms"
            st.rerun()
    with m4:
        if st.button("Settings & Backups", use_container_width=True, key="hub_settings"):
            st.session_state.current_page = "settings"
            st.rerun()
