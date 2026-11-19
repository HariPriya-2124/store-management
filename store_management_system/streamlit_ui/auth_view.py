"""
Authentication View for Store Management System.
Clean, modern, human-designed login and registration portal.
"""

import streamlit as st
from utils.validators import validate_email
from streamlit_ui.ui_helpers import render_html

REGISTERED_USERS = {
    "admin@supermarket.com": {"password": "admin123", "name": "Store Administrator", "role": "Admin"},
    "cashier@supermarket.com": {"password": "cashier123", "name": "Sarah Miller", "role": "Cashier"},
    "manager@supermarket.com": {"password": "manager123", "name": "David Clark", "role": "Inventory Manager"},
}


def render_auth_view():
    """Renders a clean, centered login and registration interface."""
    _, col, _ = st.columns([1, 1.3, 1])

    with col:
        render_html(
            """
            <div style="text-align: center; margin: 2rem 0 1.5rem 0;">
                <div style="width: 52px; height: 52px; border-radius: 12px; background: #028090; color: white; display: inline-flex; align-items: center; justify-content: center; font-size: 1.6rem; margin-bottom: 0.75rem;">
                    🛒
                </div>
                <h2 style="margin: 0; font-size: 1.65rem; font-weight: 700; color: #0F172A;">Store Management</h2>
                <p style="margin: 4px 0 0 0; color: #64748B; font-size: 0.95rem;">Sign in to your account</p>
            </div>
            """
        )

        tab_login, tab_register = st.tabs(["Sign In", "Register"])

        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email", value="admin@supermarket.com", placeholder="name@store.com")
                password = st.text_input("Password", value="admin123", type="password")
                submit_login = st.form_submit_button("Sign In", use_container_width=True, type="primary")

                if submit_login:
                    email_clean = email.strip().lower()
                    ok, msg = validate_email(email_clean)
                    if not ok:
                        st.error(msg)
                    elif not password:
                        st.error("Please enter your password.")
                    elif email_clean in REGISTERED_USERS and REGISTERED_USERS[email_clean]["password"] == password:
                        user_info = REGISTERED_USERS[email_clean].copy()
                        user_info["email"] = email_clean
                        st.session_state.authenticated = True
                        st.session_state.user_info = user_info
                        st.session_state.current_page = "hub"
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")

            render_html("<div style='height: 10px;'></div>")
            st.caption("Quick Demo Access:")
            d1, d2, d3 = st.columns(3)
            with d1:
                if st.button("Admin", use_container_width=True):
                    u = REGISTERED_USERS["admin@supermarket.com"].copy()
                    u["email"] = "admin@supermarket.com"
                    st.session_state.authenticated = True
                    st.session_state.user_info = u
                    st.session_state.current_page = "hub"
                    st.rerun()
            with d2:
                if st.button("Cashier", use_container_width=True):
                    u = REGISTERED_USERS["cashier@supermarket.com"].copy()
                    u["email"] = "cashier@supermarket.com"
                    st.session_state.authenticated = True
                    st.session_state.user_info = u
                    st.session_state.current_page = "hub"
                    st.rerun()
            with d3:
                if st.button("Manager", use_container_width=True):
                    u = REGISTERED_USERS["manager@supermarket.com"].copy()
                    u["email"] = "manager@supermarket.com"
                    st.session_state.authenticated = True
                    st.session_state.user_info = u
                    st.session_state.current_page = "hub"
                    st.rerun()

        with tab_register:
            with st.form("register_form"):
                reg_name = st.text_input("Full Name", value="", placeholder="e.g. Alex Johnson")
                reg_role = st.selectbox("Role", ["Cashier", "Inventory Manager", "Admin"])
                reg_email = st.text_input("Email", value="")
                reg_pass = st.text_input("Password", value="", type="password")
                submit_reg = st.form_submit_button("Create Account", use_container_width=True, type="primary")

                if submit_reg:
                    email_clean = reg_email.strip().lower()
                    ok, msg = validate_email(email_clean)
                    if not ok:
                        st.error(msg)
                    elif not reg_name.strip():
                        st.error("Please enter your name.")
                    elif len(reg_pass) < 4:
                        st.error("Password must be at least 4 characters.")
                    else:
                        REGISTERED_USERS[email_clean] = {"password": reg_pass, "name": reg_name.strip(), "role": reg_role}
                        user_info = {"name": reg_name.strip(), "role": reg_role, "email": email_clean}
                        st.session_state.authenticated = True
                        st.session_state.user_info = user_info
                        st.session_state.current_page = "hub"
                        st.rerun()
