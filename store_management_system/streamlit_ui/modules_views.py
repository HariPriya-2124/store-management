"""
Extended Views for Store Management System.
Point of Sale, Inventory Movements, Analytics, Suppliers, and Settings.
Clean, modern, human-designed interface without excessive AI buzzwords.
"""

from datetime import date, datetime
import streamlit as st
import pandas as pd

from utils.helpers import format_currency, generate_next_id, safe_float, safe_int
from streamlit_ui.ui_helpers import render_html


# -----------------------------------------------------------------------------
# 1. POINT OF SALE
# -----------------------------------------------------------------------------
def render_sales_view(storage):
    render_html(
        """
        <div style="margin-bottom: 1.5rem;">
            <h2 style="margin: 0; font-size: 1.75rem; color: #0F172A; font-weight: 700;">Point of Sale</h2>
            <p style="margin: 4px 0 0 0; color: #64748B; font-size: 0.95rem;">Checkout terminal and receipts</p>
        </div>
        """
    )

    if "cart" not in st.session_state:
        st.session_state.cart = []

    c_catalog, c_cart = st.columns([1.2, 1.8], gap="large")

    df_prod = storage.get_products()

    with c_catalog:
        st.markdown("##### Select Product")
        if df_prod.empty:
            st.warning("No products available to sell.")
        else:
            prod_choices = {
                f"{r['product_name']} ({format_currency(safe_float(r['selling_price']))}) [Stock: {r['stock_quantity']}]": r["product_id"]
                for _, r in df_prod.iterrows()
            }
            chosen_label = st.selectbox("Product", list(prod_choices.keys()))
            chosen_pid = prod_choices[chosen_label]
            item_row = df_prod[df_prod["product_id"] == chosen_pid].iloc[0]

            avail_stock = safe_int(item_row["stock_quantity"])
            sell_price = safe_float(item_row["selling_price"])

            qty_to_buy = st.number_input("Quantity", min_value=1, max_value=max(1, avail_stock), value=1)

            if avail_stock <= 0:
                st.error("Out of stock.")
            else:
                if st.button("Add to Cart", type="primary", use_container_width=True):
                    existing = next((i for i in st.session_state.cart if i["product_id"] == chosen_pid), None)
                    if existing:
                        new_q = existing["qty"] + qty_to_buy
                        if new_q > avail_stock:
                            st.warning(f"Exceeds available stock ({avail_stock}).")
                        else:
                            existing["qty"] = new_q
                            existing["subtotal"] = existing["qty"] * sell_price
                            st.rerun()
                    else:
                        st.session_state.cart.append({
                            "product_id": chosen_pid,
                            "product_name": item_row["product_name"],
                            "price": sell_price,
                            "qty": qty_to_buy,
                            "subtotal": qty_to_buy * sell_price,
                        })
                        st.rerun()

    with c_cart:
        st.markdown("##### Current Cart & Receipt")
        if not st.session_state.cart:
            st.info("The cart is empty. Select products on the left to begin billing.")
        else:
            cart_df = pd.DataFrame(st.session_state.cart)
            subtotal = float(cart_df["subtotal"].sum())
            tax_amount = subtotal * 0.05
            grand_total = subtotal + tax_amount

            receipt_items_html = ""
            for item in st.session_state.cart:
                receipt_items_html += f"""
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem; padding: 4px 0; border-bottom: 1px dotted #E2E8F0;">
                    <span>{item['qty']}x {item['product_name']}</span>
                    <span>{format_currency(item['subtotal'])}</span>
                </div>
                """

            render_html(
                f"""
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 1.2rem; box-shadow: 0 2px 10px rgba(0,0,0,0.03);">
                    <div style="text-align: center; border-bottom: 1px solid #E2E8F0; padding-bottom: 0.8rem; margin-bottom: 0.8rem;">
                        <h4 style="margin: 0; font-size: 1.15rem; color: #0F172A;">Store Receipt</h4>
                        <div style="font-size: 0.78rem; color: #64748B;">Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
                    </div>
                    {receipt_items_html}
                    <div style="margin-top: 0.8rem; padding-top: 0.8rem; border-top: 1px solid #E2E8F0; font-size: 0.9rem;">
                        <div style="display: flex; justify-content: space-between; color: #64748B;">
                            <span>Subtotal</span>
                            <span>{format_currency(subtotal)}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; color: #64748B; margin-top: 2px;">
                            <span>GST (5%)</span>
                            <span>{format_currency(tax_amount)}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; font-weight: 700; font-size: 1.1rem; color: #0F172A; margin-top: 6px;">
                            <span>Total</span>
                            <span>{format_currency(grand_total)}</span>
                        </div>
                    </div>
                </div>
                """
            )

            pay_method = st.selectbox("Payment Method", ["Cash", "UPI / QR", "Credit Card", "Debit Card"])
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("Complete Checkout", type="primary", use_container_width=True):
                    all_ok = True
                    for item in st.session_state.cart:
                        sale_payload = {
                            "product_id": item["product_id"],
                            "quantity": item["qty"],
                            "unit_price": item["price"],
                            "total_amount": item["subtotal"],
                            "payment_method": pay_method,
                            "sale_date": date.today().strftime("%Y-%m-%d"),
                        }
                        ok, msg = storage.record_sale(sale_payload)
                        if not ok:
                            st.error(f"Error on {item['product_name']}: {msg}")
                            all_ok = False
                            break

                    if all_ok:
                        st.success(f"Payment received ({format_currency(grand_total)} via {pay_method}). Stock updated.")
                        st.session_state.cart = []
                        st.rerun()

            with col_b2:
                if st.button("Clear Cart", use_container_width=True):
                    st.session_state.cart = []
                    st.rerun()


# -----------------------------------------------------------------------------
# 2. INVENTORY MOVEMENTS
# -----------------------------------------------------------------------------
def render_inventory_view(storage):
    render_html(
        """
        <div style="margin-bottom: 1.5rem;">
            <h2 style="margin: 0; font-size: 1.75rem; color: #0F172A; font-weight: 700;">Inventory Movements</h2>
            <p style="margin: 4px 0 0 0; color: #64748B; font-size: 0.95rem;">Stock receiving, damage write-offs, and adjustments</p>
        </div>
        """
    )

    t_hist, t_add = st.tabs(["Movement History", "Record Movement"])

    with t_hist:
        df_mov = storage.get_stock_movements()
        if df_mov.empty:
            st.info("No inventory movements recorded yet.")
        else:
            st.dataframe(
                df_mov,
                column_config={
                    "movement_id": st.column_config.TextColumn("ID", width="small"),
                    "product_id": st.column_config.TextColumn("Product ID", width="small"),
                    "movement_date": st.column_config.TextColumn("Date", width="small"),
                    "movement_type": st.column_config.TextColumn("Type", width="small"),
                    "quantity_change": st.column_config.NumberColumn("Change", width="small"),
                    "notes": st.column_config.TextColumn("Notes", width="large"),
                },
                use_container_width=True,
                hide_index=True,
            )

    with t_add:
        df_prod = storage.get_products()
        if df_prod.empty:
            st.warning("No products available.")
        else:
            prod_choices = {f"{r['product_name']} ({r['product_id']})": r["product_id"] for _, r in df_prod.iterrows()}
            with st.form("record_movement_form"):
                sel_label = st.selectbox("Product", list(prod_choices.keys()))
                sel_pid = prod_choices[sel_label]

                col1, col2 = st.columns(2)
                with col1:
                    m_type = st.selectbox("Movement Type", ["STOCK_IN", "DAMAGE_OUT", "ADJUSTMENT"])
                    qty = st.number_input("Quantity Change", min_value=1, value=10)
                with col2:
                    m_date = st.date_input("Date", value=date.today())
                    notes = st.text_input("Notes", value="Standard receiving")

                submit_mov = st.form_submit_button("Record Movement", type="primary")

                if submit_mov:
                    final_qty = qty if m_type == "STOCK_IN" else -qty
                    row = df_prod[df_prod["product_id"] == sel_pid].iloc[0]
                    curr_q = safe_int(row["stock_quantity"])

                    if final_qty < 0 and curr_q + final_qty < 0:
                        st.error(f"Cannot deduct {qty} units. Current stock is {curr_q}.")
                    else:
                        storage.update_product_stock(sel_pid, curr_q + final_qty)
                        mov_id = generate_next_id("MOV-", storage.get_stock_movements()["movement_id"].tolist() if not storage.get_stock_movements().empty else [])
                        storage.record_movement({
                            "movement_id": mov_id,
                            "product_id": sel_pid,
                            "movement_date": m_date.strftime("%Y-%m-%d"),
                            "movement_type": m_type,
                            "quantity_change": str(final_qty),
                            "notes": notes,
                        })
                        st.success(f"Recorded {m_type} of {qty} units for {sel_pid}.")
                        st.rerun()


# -----------------------------------------------------------------------------
# 3. ANALYTICS
# -----------------------------------------------------------------------------
def render_analytics_view(storage):
    render_html(
        """
        <div style="margin-bottom: 1.5rem;">
            <h2 style="margin: 0; font-size: 1.75rem; color: #0F172A; font-weight: 700;">Analytics</h2>
            <p style="margin: 4px 0 0 0; color: #64748B; font-size: 0.95rem;">Sales and inventory performance metrics</p>
        </div>
        """
    )

    df_sales = storage.get_sales()
    df_prod = storage.get_products()

    if df_sales.empty:
        st.info("No sales data available to analyze.")
        return

    tot_rev = float(pd.to_numeric(df_sales["total_amount"], errors="coerce").fillna(0.0).sum())
    tot_units = int(pd.to_numeric(df_sales["quantity_sold"], errors="coerce").fillna(0).sum())
    avg_ticket = tot_rev / len(df_sales) if len(df_sales) > 0 else 0.0

    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Gross Revenue", format_currency(tot_rev))
    a2.metric("Units Sold", f"{tot_units:,}")
    a3.metric("Average Basket", format_currency(avg_ticket))
    a4.metric("Catalog SKUs", f"{len(df_prod):,}")

    render_html("<div style='height: 15px;'></div>")
    c1, c2 = st.columns(2)

    with c1:
        with st.container(border=True):
            st.markdown("##### Inventory by Category")
            df_prod["stock_num"] = pd.to_numeric(df_prod["stock_quantity"], errors="coerce").fillna(0)
            cat_stock = df_prod.groupby("category")["stock_num"].sum().reset_index()
            cat_stock = cat_stock.rename(columns={"category": "Category", "stock_num": "Units in Stock"})
            st.bar_chart(cat_stock.set_index("Category"))

    with c2:
        with st.container(border=True):
            st.markdown("##### Top Selling Products by Revenue")
            p_cols = [c for c in ["product_id", "product_name", "category"] if c in df_prod.columns]
            sales_clean = df_sales.drop(columns=[c for c in ["product_name", "category"] if c in df_sales.columns], errors="ignore")
            merged = sales_clean.merge(df_prod[p_cols], on="product_id", how="left")
            merged["rev_num"] = pd.to_numeric(merged["total_amount"], errors="coerce").fillna(0)
            merged["product_name"] = merged["product_name"].fillna(merged["product_id"])
            prod_rev = merged.groupby("product_name")["rev_num"].sum().nlargest(10).reset_index()
            prod_rev = prod_rev.rename(columns={"product_name": "Product", "rev_num": "Revenue (INR ₹)"})
            st.bar_chart(prod_rev.set_index("Product"))


# -----------------------------------------------------------------------------
# 4. SUPPLIERS DIRECTORY
# -----------------------------------------------------------------------------
def render_suppliers_view(storage):
    render_html(
        """
        <div style="margin-bottom: 1.5rem;">
            <h2 style="margin: 0; font-size: 1.75rem; color: #0F172A; font-weight: 700;">Suppliers</h2>
            <p style="margin: 4px 0 0 0; color: #64748B; font-size: 0.95rem;">Vendor directory and contact details</p>
        </div>
        """
    )

    t_list, t_add = st.tabs(["Supplier Directory", "Add Supplier"])

    with t_list:
        df_supp = storage.get_suppliers()
        if df_supp.empty:
            st.info("No suppliers currently listed.")
        else:
            st.dataframe(
                df_supp,
                column_config={
                    "supplier_id": st.column_config.TextColumn("ID", width="small"),
                    "supplier_name": st.column_config.TextColumn("Supplier Name", width="medium"),
                    "contact_person": st.column_config.TextColumn("Contact", width="small"),
                    "phone": st.column_config.TextColumn("Phone", width="small"),
                    "email": st.column_config.TextColumn("Email", width="small"),
                },
                use_container_width=True,
                hide_index=True,
            )

    with t_add:
        with st.form("new_supplier_form"):
            df_supp = storage.get_suppliers()
            sid = generate_next_id("SUP-", df_supp["supplier_id"].tolist() if not df_supp.empty else [])
            s_name = st.text_input("Supplier Name")
            s_contact = st.text_input("Contact Person")
            col1, col2 = st.columns(2)
            with col1:
                s_phone = st.text_input("Phone", value="+91 98765 00000")
            with col2:
                s_email = st.text_input("Email", value="orders@vendor.com")

            submit_sup = st.form_submit_button("Save Supplier", type="primary")

            if submit_sup:
                if not s_name.strip():
                    st.error("Please enter a supplier name.")
                else:
                    new_sup = {
                        "supplier_id": sid,
                        "supplier_name": s_name.strip(),
                        "contact_person": s_contact.strip(),
                        "phone": s_phone.strip(),
                        "email": s_email.strip(),
                    }
                    ok, msg = storage.add_supplier(new_sup)
                    if ok:
                        st.success(f"Supplier '{s_name}' saved.")
                        st.rerun()
                    else:
                        st.error(msg)


# -----------------------------------------------------------------------------
# 5. SETTINGS & BACKUPS
# -----------------------------------------------------------------------------
def render_settings_view(storage):
    render_html(
        """
        <div style="margin-bottom: 1.5rem;">
            <h2 style="margin: 0; font-size: 1.75rem; color: #0F172A; font-weight: 700;">Settings & Backups</h2>
            <p style="margin: 4px 0 0 0; color: #64748B; font-size: 0.95rem;">System configuration and data snapshots</p>
        </div>
        """
    )

    st.markdown("##### Data Backups")
    st.caption("Create manual snapshots or restore from previously saved archives.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Create Backup Snapshot", type="primary", use_container_width=True):
            res = storage.backup_mgr.create_backup("manual")
            ok, msg = res[0], res[1]
            if ok:
                st.success(msg)
            else:
                st.error(msg)

    with col2:
        backups = storage.backup_mgr.list_backups()
        if not backups:
            st.info("No backup archives found.")
        else:
            b_choices = [b["filename"] for b in backups if "filename" in b]
            if b_choices:
                sel_b = st.selectbox("Select Snapshot", b_choices)
                if st.button("Restore Selected Snapshot", use_container_width=True):
                    ok, msg = storage.backup_mgr.restore_backup(sel_b)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
