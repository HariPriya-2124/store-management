"""
Core Product Views for Store Management System.
Includes Add Product, Catalog Explorer, Edit Product, Delete Product, Expiry Alerts, and SMS Notifications.
Clean, professional, human-designed interface without excessive AI buzzwords.
"""

import re
from datetime import date, datetime, timedelta
import streamlit as st
import pandas as pd

from utils.helpers import format_currency, generate_next_id, safe_float, safe_int
from utils.validators import validate_product_data
from utils.sms_service import dispatch_sms, normalize_phone_number, get_whatsapp_url
from streamlit_ui.ui_helpers import render_html


# -----------------------------------------------------------------------------
# 1. ADD PRODUCT
# -----------------------------------------------------------------------------
def render_create_view(storage):
    render_html(
        """
        <div style="margin-bottom: 1.5rem;">
            <h2 style="margin: 0; font-size: 1.75rem; color: #0F172A; font-weight: 700;">Add Product</h2>
            <p style="margin: 4px 0 0 0; color: #64748B; font-size: 0.95rem;">Enter product details to add a new item to inventory</p>
        </div>
        """
    )

    df_prod = storage.get_products()
    existing_pids = df_prod["product_id"].tolist() if not df_prod.empty else []
    next_pid = generate_next_id("PRD-", existing_pids)

    df_supp = storage.get_suppliers()
    supp_options = {
        f"{s['supplier_name']} ({s['supplier_id']})": s["supplier_id"]
        for _, s in df_supp.iterrows()
    } if not df_supp.empty else {"General Supplier (SUP-001)": "SUP-001"}

    col_form, col_preview = st.columns([1.5, 1], gap="large")

    with col_form:
        with st.form("create_product_form"):
            st.markdown("##### Product Information")
            c1, c2 = st.columns(2)
            with c1:
                pname = st.text_input("Product Name", placeholder="e.g. Organic Rolled Oats 500g")
                sku = st.text_input("SKU", value=f"SKU-{next_pid.replace('PRD-', '')}")
            with c2:
                categories = ["Beverages", "Snacks", "Dairy & Eggs", "Bakery", "Produce", "Pantry", "Personal Care", "Cleaning"]
                category = st.selectbox("Category", categories)
                barcode = st.text_input("Barcode", value=f"890100{next_pid.replace('PRD-', '')}01")

            st.markdown("##### Pricing & Stock")
            p1, p2 = st.columns(2)
            with p1:
                buy_price = st.number_input("Cost Price (₹)", min_value=0.0, value=25.0, step=5.0)
                sell_price = st.number_input("Selling Price (₹)", min_value=0.0, value=40.0, step=5.0)
            with p2:
                stock_qty = st.number_input("Initial Quantity", min_value=0, value=50, step=1)
                reorder_pt = st.number_input("Reorder Threshold", min_value=1, value=10, step=1)

            st.markdown("##### Supplier & Expiry")
            s1, s2 = st.columns(2)
            with s1:
                supplier_label = st.selectbox("Supplier", list(supp_options.keys()))
                supplier_id = supp_options[supplier_label]
            with s2:
                exp_date = st.date_input("Expiration Date", value=date.today() + timedelta(days=180))

            submit_btn = st.form_submit_button("Save Product", type="primary", use_container_width=True)

            if submit_btn:
                ok, msg, clean_prod = validate_product_data(
                    product_id=next_pid,
                    product_name=pname,
                    category=category,
                    supplier_id=supplier_id,
                    purchase_price=buy_price,
                    selling_price=sell_price,
                    stock_quantity=stock_qty,
                    minimum_stock=reorder_pt,
                    expiry_date=exp_date.strftime("%Y-%m-%d"),
                    existing_product_ids=existing_pids,
                    is_update=False,
                )
                if not ok:
                    st.error(msg)
                else:
                    clean_prod["sku"] = sku.strip()
                    clean_prod["barcode"] = barcode.strip()
                    clean_prod["purchase_price"] = f"{buy_price:.2f}"
                    clean_prod["selling_price"] = f"{sell_price:.2f}"
                    clean_prod["minimum_stock"] = int(reorder_pt)
                    clean_prod["stock_quantity"] = int(stock_qty)
                    success, save_msg = storage.add_product(clean_prod)
                    if success:
                        st.success(f"Product '{pname}' saved with ID {next_pid}.")
                        st.session_state.current_page = "op_read"
                        st.rerun()
                    else:
                        st.error(save_msg)

    with col_preview:
        st.markdown("##### Pricing Summary")
        unit_profit = sell_price - buy_price
        margin_pct = (unit_profit / sell_price * 100) if sell_price > 0 else 0
        profit_color = "#10B981" if unit_profit >= 0 else "#EF4444"

        render_html(
            f"""
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 1.2rem; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
                <div style="font-size: 0.8rem; color: #64748B; font-weight: 600;">ESTIMATED PROFIT PER UNIT</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: {profit_color}; margin: 4px 0;">
                    {format_currency(unit_profit)}
                </div>
                <div style="font-size: 0.85rem; color: #475569;">
                    Gross Margin: <strong style="color: {profit_color};">{margin_pct:.1f}%</strong>
                </div>
                <hr style="margin: 0.8rem 0; border: none; border-top: 1px solid #F1F5F9;">
                <div style="font-size: 0.82rem; color: #64748B; line-height: 1.6;">
                    Total Cost: <strong>{format_currency(buy_price * stock_qty)}</strong><br>
                    Expected Revenue: <strong>{format_currency(sell_price * stock_qty)}</strong>
                </div>
            </div>
            """
        )


# -----------------------------------------------------------------------------
# 2. PRODUCT CATALOG
# -----------------------------------------------------------------------------
def render_retrieve_view(storage):
    render_html(
        """
        <div style="margin-bottom: 1.5rem;">
            <h2 style="margin: 0; font-size: 1.75rem; color: #0F172A; font-weight: 700;">Products</h2>
            <p style="margin: 4px 0 0 0; color: #64748B; font-size: 0.95rem;">Browse, search, and manage inventory</p>
        </div>
        """
    )

    df_prod = storage.get_products()
    if df_prod.empty:
        st.info("No products currently in the catalog.")
        return

    # Financial Summary
    total_retail_val = float((pd.to_numeric(df_prod.get("selling_price", 0), errors="coerce").fillna(0) * pd.to_numeric(df_prod.get("stock_quantity", 0), errors="coerce").fillna(0)).sum())
    cost_col = "purchase_price" if "purchase_price" in df_prod.columns else ("buying_price" if "buying_price" in df_prod.columns else None)
    total_cost_val = float((pd.to_numeric(df_prod[cost_col], errors="coerce").fillna(0) * pd.to_numeric(df_prod.get("stock_quantity", 0), errors="coerce").fillna(0)).sum()) if cost_col else 0.0

    threshold_col = "minimum_stock" if "minimum_stock" in df_prod.columns else ("reorder_level" if "reorder_level" in df_prod.columns else None)
    low_stock_count = int((pd.to_numeric(df_prod["stock_quantity"], errors="coerce").fillna(0) <= pd.to_numeric(df_prod[threshold_col], errors="coerce").fillna(0)).sum()) if threshold_col else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Items", f"{len(df_prod):,}")
    m2.metric("Total Retail Value", format_currency(total_retail_val))
    m3.metric("Inventory Cost Value", format_currency(total_cost_val))
    m4.metric("Low Stock Items", f"{low_stock_count}", delta=f"{low_stock_count} low" if low_stock_count > 0 else None, delta_color="inverse")

    render_html("<div style='height: 10px;'></div>")

    # Search & Filter
    f1, f2, f3 = st.columns([2, 1, 1])
    with f1:
        search_query = st.text_input("Search Products", placeholder="Search by name, SKU, or ID...")
    with f2:
        all_cats = ["All Categories"] + sorted(list(df_prod["category"].dropna().unique()))
        selected_cat = st.selectbox("Category", all_cats)
    with f3:
        stock_filter = st.selectbox("Stock Status", ["All Items", "In Stock", "Low Stock", "Out of Stock"])

    filtered = df_prod.copy()

    if search_query.strip():
        q = search_query.strip().lower()
        filtered = filtered[
            filtered["product_name"].str.lower().str.contains(q, na=False)
            | filtered["product_id"].str.lower().str.contains(q, na=False)
            | (filtered["sku"].str.lower().str.contains(q, na=False) if "sku" in filtered.columns else False)
        ]

    if selected_cat != "All Categories":
        filtered = filtered[filtered["category"] == selected_cat]

    threshold_s = pd.to_numeric(filtered[threshold_col], errors="coerce").fillna(0) if threshold_col else 0
    stock_s = pd.to_numeric(filtered["stock_quantity"], errors="coerce").fillna(0)
    if stock_filter == "Low Stock":
        filtered = filtered[(stock_s <= threshold_s) & (stock_s > 0)]
    elif stock_filter == "Out of Stock":
        filtered = filtered[stock_s <= 0]
    elif stock_filter == "In Stock":
        filtered = filtered[stock_s > threshold_s]

    display_df = filtered.copy()
    if "selling_price" in display_df.columns:
        display_df["selling_price"] = display_df["selling_price"].apply(lambda v: format_currency(safe_float(v)))
    if "purchase_price" in display_df.columns:
        display_df["purchase_price"] = display_df["purchase_price"].apply(lambda v: format_currency(safe_float(v)))
    elif "buying_price" in display_df.columns:
        display_df["buying_price"] = display_df["buying_price"].apply(lambda v: format_currency(safe_float(v)))

    st.dataframe(
        display_df,
        column_config={
            "product_id": st.column_config.TextColumn("ID", width="small"),
            "product_name": st.column_config.TextColumn("Product Name", width="medium"),
            "category": st.column_config.TextColumn("Category", width="small"),
            "selling_price": st.column_config.TextColumn("Selling Price", width="small"),
            "purchase_price": st.column_config.TextColumn("Cost Price", width="small"),
            "stock_quantity": st.column_config.NumberColumn("Stock", width="small"),
            "minimum_stock": st.column_config.NumberColumn("Min Stock", width="small"),
            "expiry_date": st.column_config.TextColumn("Expiry Date", width="small"),
            "supplier_id": st.column_config.TextColumn("Supplier ID", width="small"),
        },
        use_container_width=True,
        hide_index=True,
    )

    csv_data = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Export CSV",
        data=csv_data,
        file_name=f"products_{date.today()}.csv",
        mime="text/csv",
    )


# -----------------------------------------------------------------------------
# 3. EDIT PRODUCT
# -----------------------------------------------------------------------------
def render_update_view(storage):
    render_html(
        """
        <div style="margin-bottom: 1.5rem;">
            <h2 style="margin: 0; font-size: 1.75rem; color: #0F172A; font-weight: 700;">Edit Product</h2>
            <p style="margin: 4px 0 0 0; color: #64748B; font-size: 0.95rem;">Update product details, pricing, or stock counts</p>
        </div>
        """
    )

    df_prod = storage.get_products()
    if df_prod.empty:
        st.warning("No products available to edit.")
        return

    prod_options = {
        f"{r['product_name']} ({r['product_id']})": r["product_id"]
        for _, r in df_prod.iterrows()
    }

    selected_label = st.selectbox("Select Product", list(prod_options.keys()))
    selected_pid = prod_options[selected_label]
    row = df_prod[df_prod["product_id"] == selected_pid].iloc[0]

    df_supp = storage.get_suppliers()
    supp_options = {f"{s['supplier_name']} ({s['supplier_id']})": s["supplier_id"] for _, s in df_supp.iterrows()} if not df_supp.empty else {"General (SUP-001)": "SUP-001"}

    with st.form("update_product_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### Details")
            u_name = st.text_input("Product Name", value=row["product_name"])
            u_cat = st.text_input("Category", value=row["category"])
            u_sku = st.text_input("SKU", value=row.get("sku", ""))
            u_barcode = st.text_input("Barcode", value=row.get("barcode", ""))

        with col2:
            st.markdown("##### Pricing & Inventory")
            cost_val = safe_float(row.get("purchase_price", row.get("buying_price", 0.0)))
            thresh_val = safe_int(row.get("minimum_stock", row.get("reorder_level", 10)))
            u_buy = st.number_input("Cost Price (₹)", min_value=0.0, value=cost_val, step=5.0)
            u_sell = st.number_input("Selling Price (₹)", min_value=0.0, value=safe_float(row["selling_price"]), step=5.0)
            u_stock = st.number_input("Stock Quantity", min_value=0, value=safe_int(row["stock_quantity"]), step=1)
            u_reorder = st.number_input("Minimum Threshold", min_value=1, value=thresh_val, step=1)

        curr_sid = row.get("supplier_id", "")
        supp_keys = list(supp_options.keys())
        default_idx = 0
        for i, k in enumerate(supp_keys):
            if supp_options[k] == curr_sid:
                default_idx = i
                break
        u_supp_label = st.selectbox("Supplier", supp_keys, index=default_idx)
        u_supp_id = supp_options[u_supp_label]

        save_update = st.form_submit_button("Save Changes", type="primary", use_container_width=True)

        if save_update:
            updated_dict = {
                "product_name": u_name.strip(),
                "category": u_cat.strip(),
                "sku": u_sku.strip(),
                "barcode": u_barcode.strip(),
                "purchase_price": f"{u_buy:.2f}",
                "selling_price": f"{u_sell:.2f}",
                "stock_quantity": int(u_stock),
                "minimum_stock": int(u_reorder),
                "supplier_id": u_supp_id,
                "expiry_date": row.get("expiry_date", ""),
            }
            ok, msg = storage.update_product(selected_pid, updated_dict)
            if ok:
                st.success(f"Product '{selected_pid}' updated.")
                st.session_state.current_page = "op_read"
                st.rerun()
            else:
                st.error(msg)


# -----------------------------------------------------------------------------
# 4. DELETE PRODUCT
# -----------------------------------------------------------------------------
def render_delete_view(storage):
    render_html(
        """
        <div style="margin-bottom: 1.5rem;">
            <h2 style="margin: 0; font-size: 1.75rem; color: #0F172A; font-weight: 700;">Delete Product</h2>
            <p style="margin: 4px 0 0 0; color: #64748B; font-size: 0.95rem;">Remove an item from active inventory</p>
        </div>
        """
    )

    df_prod = storage.get_products()
    if df_prod.empty:
        st.info("No products available to delete.")
        return

    prod_options = {
        f"{r['product_name']} ({r['product_id']})": r["product_id"]
        for _, r in df_prod.iterrows()
    }

    selected_label = st.selectbox("Select Product to Remove", list(prod_options.keys()))
    selected_pid = prod_options[selected_label]
    row = df_prod[df_prod["product_id"] == selected_pid].iloc[0]

    with st.container(border=True):
        st.markdown(f"**Item:** {row['product_name']} (`{selected_pid}`)")
        st.markdown(f"**Category:** {row['category']} • **Stock:** {row['stock_quantity']} • **Price:** {format_currency(safe_float(row['selling_price']))}")
        confirm_check = st.checkbox("Confirm deletion")
        del_button = st.button("Delete Product", type="primary", disabled=not confirm_check)

        if del_button:
            ok, msg = storage.delete_product(selected_pid)
            if ok:
                st.success(f"Product '{selected_pid}' removed.")
                st.session_state.current_page = "op_read"
                st.rerun()
            else:
                st.error(msg)


# -----------------------------------------------------------------------------
# 5. EXPIRY ALERTS
# -----------------------------------------------------------------------------
def render_expiry_view(storage):
    render_html(
        """
        <div style="margin-bottom: 1.5rem;">
            <h2 style="margin: 0; font-size: 1.75rem; color: #0F172A; font-weight: 700;">Expiry Alerts</h2>
            <p style="margin: 4px 0 0 0; color: #64748B; font-size: 0.95rem;">Track batches approaching their shelf-life limits</p>
        </div>
        """
    )

    storage.refresh_expiry_alerts()
    df_exp = storage.get_expiry_alerts()

    if df_exp.empty:
        st.success("No active expiry warnings. All inventory batches have valid shelf life.")
        return

    days_col = pd.to_numeric(df_exp["days_until_expiry"], errors="coerce").fillna(999)
    crit_count = int((days_col <= 7).sum())
    warn_count = int(((days_col > 7) & (days_col <= 30)).sum())
    healthy_count = int((days_col > 30).sum())

    e1, e2, e3 = st.columns(3)
    e1.metric("Critical (≤ 7 Days)", f"{crit_count}", delta="Urgent" if crit_count > 0 else None, delta_color="inverse")
    e2.metric("Warning (8–30 Days)", f"{warn_count}")
    e3.metric("Normal (> 30 Days)", f"{healthy_count}")

    render_html("<div style='height: 10px;'></div>")
    st.dataframe(
        df_exp,
        column_config={
            "alert_id": st.column_config.TextColumn("Alert ID", width="small"),
            "product_id": st.column_config.TextColumn("Product ID", width="small"),
            "product_name": st.column_config.TextColumn("Product", width="medium"),
            "category": st.column_config.TextColumn("Category", width="small"),
            "batch_expiry_date": st.column_config.TextColumn("Expiry Date", width="small"),
            "days_until_expiry": st.column_config.NumberColumn("Days Left", width="small"),
            "alert_status": st.column_config.TextColumn("Status", width="small"),
            "notification_sent": st.column_config.TextColumn("Notes", width="medium"),
        },
        use_container_width=True,
        hide_index=True,
    )

    render_html("<div style='height: 10px;'></div>")
    with st.container(border=True):
        st.markdown("##### Process Batch Action")
        with st.form("disposal_form"):
            alert_choices = {f"{r['product_name']} ({r['days_until_expiry']} days left)": r["alert_id"] for _, r in df_exp.iterrows()}
            selected_alert_label = st.selectbox("Select Batch", list(alert_choices.keys()))
            selected_alert_id = alert_choices[selected_alert_label]

            d_col1, d_col2 = st.columns(2)
            with d_col1:
                disposal_reason = st.selectbox("Action", ["Discount Clearance", "Damaged / Expired Write-Off", "Vendor Return"])
            with d_col2:
                notes = st.text_input("Notes", value="Reviewed by Manager")

            submit_disposal = st.form_submit_button("Submit Action", type="primary")

            if submit_disposal:
                storage.update_alert_notification(selected_alert_id, new_status=f"{disposal_reason} ({notes})")
                st.success("Batch updated.")
                st.rerun()


# -----------------------------------------------------------------------------
# 6. SMS NOTIFICATIONS
# -----------------------------------------------------------------------------
def render_sms_view(storage):
    render_html(
        """
        <div style="margin-bottom: 1.5rem;">
            <h2 style="margin: 0; font-size: 1.75rem; color: #0F172A; font-weight: 700;">SMS Notifications</h2>
            <p style="margin: 4px 0 0 0; color: #64748B; font-size: 0.95rem;">Send SMS alerts to any mobile number, suppliers, or staff</p>
        </div>
        """
    )

    t1, t2 = st.tabs(["Send SMS", "Dispatch History"])

    with t1:
        col_form, col_preview = st.columns([1.4, 1], gap="large")

        # 1. Recipient Selection
        with col_form:
            st.markdown("##### 1. Select Recipient")
            recipient_source = st.radio(
                "Recipient Source",
                ["Enter Mobile Number", "From Supplier Directory", "From Expiry Alerts"],
                horizontal=True,
                label_visibility="collapsed",
            )

            target_phone = ""
            target_name = "Contact"
            linked_alert_id = None
            default_template = "Restock Notice"

            if recipient_source == "Enter Mobile Number":
                c_p1, c_p2 = st.columns([1.5, 1])
                with c_p1:
                    target_phone = st.text_input("Recipient Mobile Number", value="+91 98765 43210", placeholder="+91 98765 43210 or 10-digit number")
                with c_p2:
                    target_name = st.text_input("Contact Name", value="Customer / Staff", placeholder="e.g. John Doe")

            elif recipient_source == "From Supplier Directory":
                df_supp = storage.get_suppliers()
                if df_supp.empty:
                    st.warning("No suppliers found in directory. Using manual entry.")
                    target_phone = st.text_input("Mobile Number", value="+91 98765 43210")
                else:
                    supp_map = {
                        f"{s['supplier_name']} ({s.get('phone', 'No Phone')})": (s.get("phone", ""), s["supplier_name"])
                        for _, s in df_supp.iterrows()
                    }
                    sel_supp_label = st.selectbox("Choose Supplier", list(supp_map.keys()))
                    target_phone, target_name = supp_map[sel_supp_label]
                    st.caption(f"Selected: **{target_name}** • Phone: `{target_phone}`")

            elif recipient_source == "From Expiry Alerts":
                df_exp = storage.get_expiry_alerts()
                if df_exp.empty:
                    st.info("No active expiry alerts found.")
                    target_phone = st.text_input("Mobile Number", value="+91 98765 43210")
                else:
                    alert_map = {
                        f"Alert {r['alert_id']} — {r.get('product_name', r['product_id'])} ({r.get('days_until_expiry', '?')}d left)": (
                            r["alert_id"],
                            r.get("product_name", r["product_id"]),
                            r.get("days_until_expiry", "0"),
                            r.get("batch_number", "BCH-101"),
                        )
                        for _, r in df_exp.iterrows()
                    }
                    sel_alert_label = st.selectbox("Choose Expiry Alert Batch", list(alert_map.keys()))
                    linked_alert_id, prod_n, days_l, bch = alert_map[sel_alert_label]
                    target_phone = st.text_input("Mobile Number for Alert Notice", value="+91 98765 43210")
                    target_name = f"Dept Mgr ({prod_n})"
                    default_template = "Expiry Alert"

            # 2. Message Composition
            st.markdown("##### 2. Message Content")
            templates = {
                "Restock Notice": f"URGENT RESTOCK: Stock for {target_name} is critically low. Please dispatch replenishment batch today. - Store Operations",
                "Expiry Alert": f"ALERT: Batch {target_name} has {target_phone} nearing shelf-life limit. Immediate clearance or write-off required. - Store Operations",
                "Order Ready": "Hi valued customer, your store pickup order is packed and ready for collection at Counter 1. Thank you!",
                "Custom Message": "Store Alert: Please review inventory update.",
            }

            sel_tmpl = st.selectbox("Quick Templates", list(templates.keys()), index=0 if default_template not in templates else list(templates.keys()).index(default_template))
            msg_body = st.text_area("SMS Body", value=templates[sel_tmpl], height=105)

            char_len = len(msg_body)
            segments = (char_len // 160) + 1
            st.caption(f"📏 {char_len} Characters • {segments} SMS segment(s)")

            # 3. Gateway Configuration
            st.markdown("##### 3. Delivery Gateway")
            gw_choice = st.selectbox(
                "Dispatch Gateway",
                [
                    "Auto (Live Telecom Network with fallback)",
                    "Fast2SMS (Real SMS to India +91 - API Key)",
                    "Twilio (Real Global SMS Gateway)",
                    "Textbelt (Real SMS - 1 Free/day or Paid Key)",
                    "Simulated Gateway (Instant Test & Telemetry)",
                ],
            )

            gw_mode = "auto"
            api_key = ""
            twilio_cfg = {}

            if "Fast2SMS" in gw_choice:
                gw_mode = "fast2sms"
                api_key = st.text_input("Fast2SMS API Key", type="password", placeholder="Enter key from fast2sms.com")
                st.caption("ℹ️ Fast2SMS delivers real carrier SMS to Indian (+91) numbers. You can get free trial credits at [fast2sms.com](https://www.fast2sms.com).")
            elif "Twilio" in gw_choice:
                gw_mode = "twilio"
                c_tw1, c_tw2 = st.columns(2)
                with c_tw1:
                    t_sid = st.text_input("Account SID", type="password", placeholder="ACxxxxxxxx")
                    t_from = st.text_input("From Phone Number", placeholder="+1xxxxxxxxxx")
                with c_tw2:
                    t_tok = st.text_input("Auth Token", type="password", placeholder="xxxxxxxxxx")
                twilio_cfg = {"account_sid": t_sid, "auth_token": t_tok, "from_phone": t_from}
            elif "Textbelt" in gw_choice:
                gw_mode = "textbelt"
                api_key = st.text_input("Textbelt API Key (leave empty for 1 free/day global)", type="password")
            elif "Simulated" in gw_choice:
                gw_mode = "simulated"
            else:
                gw_mode = "auto"

            # WhatsApp Direct Action
            clean_digits = re.sub(r"\D", "", target_phone)
            if clean_digits:
                wa_url = get_whatsapp_url(target_phone, msg_body)
                st.link_button(
                    "💬 Send to Mobile via WhatsApp (Free & Instant)",
                    wa_url,
                    use_container_width=True,
                )

            send_now = st.button("📲 Send Cellular SMS", type="primary", use_container_width=True)

            if send_now:
                with st.spinner("Dispatching SMS via telecom carrier network..."):
                    result = dispatch_sms(
                        phone_raw=target_phone,
                        message=msg_body,
                        recipient_name=target_name,
                        message_type=sel_tmpl,
                        gateway_mode=gw_mode,
                        api_key=api_key,
                        twilio_config=twilio_cfg,
                    )

                if result["success"]:
                    # Generate next SMS ID
                    existing_logs = storage.get_sms_logs()
                    existing_ids = existing_logs["sms_id"].tolist() if not existing_logs.empty and "sms_id" in existing_logs.columns else []
                    next_sms_id = generate_next_id("SMS-", existing_ids)

                    # Save to persistent storage
                    log_record = {
                        "sms_id": next_sms_id,
                        "timestamp": result["timestamp"],
                        "recipient_phone": result["phone"],
                        "recipient_name": target_name,
                        "message_type": sel_tmpl,
                        "message_body": msg_body,
                        "gateway": result["gateway"],
                        "status": result["status"],
                        "delivery_id": result["delivery_id"],
                    }
                    storage.record_sms_log(log_record)

                    # If linked to an expiry alert, update alert status
                    if linked_alert_id:
                        storage.update_alert_notification(linked_alert_id, f"SMS Sent to {result['phone']}")

                    st.success(f"✅ {result['message']}")

                    # Helpful note for India telecom policy if relevant
                    if "disabled for this country" in result.get("message", "").lower() or "+91" in result.get("phone", ""):
                        st.info("💡 **India Mobile Tip**: International free SMS providers (like Textbelt) block free web-to-mobile texts to India due to TRAI anti-spam rules. For 100% free delivery to this phone, click the **WhatsApp** button above, or enter a **Fast2SMS** key.")

                    st.balloons()
                else:
                    st.error(f"❌ Delivery Failed: {result['message']}")

        # Smartphone Preview Column
        with col_preview:
            st.markdown("##### 📱 Handset Message Preview")
            render_html(
                f"""
                <div style="background: #1E293B; border-radius: 28px; padding: 18px 16px; box-shadow: 0 15px 35px -5px rgba(0,0,0,0.25); border: 4px solid #334155; max-width: 300px; margin: 0 auto; color: white;">
                    <!-- Phone top bar & speaker -->
                    <div style="width: 70px; height: 10px; background: #0F172A; border-radius: 6px; margin: 0 auto 12px auto;"></div>
                    
                    <div style="font-size: 0.72rem; text-align: center; color: #94A3B8; margin-bottom: 12px;">
                        Messages • {target_phone or 'No Number'}
                    </div>

                    <div style="background: #028090; border-radius: 14px 14px 3px 14px; padding: 12px 14px; font-size: 0.85rem; line-height: 1.45; color: white; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
                        {msg_body}
                    </div>

                    <div style="text-align: right; font-size: 0.65rem; color: #94A3B8; margin-top: 6px;">
                        {datetime.now().strftime('%H:%M')} • Sent
                    </div>
                </div>
                """
            )

    # Tab 2: Dispatch History from CSV
    with t2:
        df_logs = storage.get_sms_logs()
        if df_logs.empty:
            st.info("No SMS dispatches recorded yet in permanent storage.")
        else:
            st.dataframe(
                df_logs,
                column_config={
                    "sms_id": st.column_config.TextColumn("ID", width="small"),
                    "timestamp": st.column_config.TextColumn("Timestamp", width="medium"),
                    "recipient_phone": st.column_config.TextColumn("Phone", width="small"),
                    "recipient_name": st.column_config.TextColumn("Recipient", width="small"),
                    "message_type": st.column_config.TextColumn("Type", width="small"),
                    "message_body": st.column_config.TextColumn("Message", width="large"),
                    "gateway": st.column_config.TextColumn("Gateway", width="small"),
                    "status": st.column_config.TextColumn("Status", width="small"),
                    "delivery_id": st.column_config.TextColumn("Delivery Ref", width="small"),
                },
                use_container_width=True,
                hide_index=True,
            )

            csv_data = df_logs.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Export SMS Logs to CSV",
                data=csv_data,
                file_name=f"sms_dispatch_logs_{date.today()}.csv",
                mime="text/csv",
            )
