import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import hashlib

# Hash function for security
def hash_string(string):
    return hashlib.sha256(string.encode()).hexdigest()

# Secure SQLite connection
@st.cache_resource
def get_db_connection():
    conn = sqlite3.connect("secure_business_manager.db", check_same_thread=False)
    return conn

# Initialize database connection
conn = get_db_connection()
cursor = conn.cursor()

# Create tables if they don't already exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    price REAL NOT NULL CHECK(price >= 0),
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    vendor TEXT NOT NULL,
    purchase_date DATE NOT NULL
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    price REAL NOT NULL CHECK(price >= 0),
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    customer TEXT NOT NULL,
    sale_date DATE NOT NULL
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    status TEXT CHECK(status IN ('Pending', 'Completed')) NOT NULL DEFAULT 'Pending',
    order_date DATE NOT NULL
)
""")
conn.commit()

# Utility functions
def add_record(table, data):
    placeholders = ', '.join(['?' for _ in data])
    query = f"INSERT INTO {table} VALUES (NULL, {placeholders})"
    cursor.execute(query, data)
    conn.commit()

def update_record_status(table, record_id, new_status):
    cursor.execute(f"""
    UPDATE {table}
    SET status = ?
    WHERE id = ?
    """, (new_status, record_id))
    conn.commit()

def fetch_data(table):
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return pd.DataFrame(rows, columns=columns)

def validate_input(**kwargs):
    for field, value in kwargs.items():
        if not value or (isinstance(value, str) and len(value.strip()) == 0):
            raise ValueError(f"{field} cannot be empty!")

# Download utility
def generate_csv_download(dataframe, file_name):
    csv = dataframe.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"Download {file_name}",
        data=csv,
        file_name=f"{file_name}.csv",
        mime="text/csv",
    )

# Streamlit app
st.title("Secure Business Manager")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Manage Purchases", "Manage Sales", "Manage Orders"])

# Manage Purchases
if page == "Manage Purchases":
    st.header("Manage Purchases")
    with st.form("purchase_form"):
        product_name = st.text_input("Product Name")
        price = st.number_input("Price", min_value=0.0, format="%.2f")
        quantity = st.number_input("Quantity", min_value=1, step=1)
        vendor = st.text_input("Vendor")
        purchase_date = st.date_input("Purchase Date", value=datetime.today())
        submit = st.form_submit_button("Add Purchase")

        if submit:
            try:
                validate_input(ProductName=product_name, Vendor=vendor)
                add_record("purchases", (product_name, price, quantity, vendor, purchase_date))
                st.success("Purchase added successfully!")
            except ValueError as e:
                st.error(e)

    st.subheader("Purchase Records")
    purchase_data = fetch_data("purchases")
    if not purchase_data.empty:
        st.dataframe(purchase_data, use_container_width=True)
        generate_csv_download(purchase_data, "Purchases")
    else:
        st.info("No purchases found.")

# Manage Sales
if page == "Manage Sales":
    st.header("Manage Sales")
    with st.form("sales_form"):
        product_name = st.text_input("Product Name")
        price = st.number_input("Price", min_value=0.0, format="%.2f")
        quantity = st.number_input("Quantity", min_value=1, step=1)
        customer = st.text_input("Customer")
        sale_date = st.date_input("Sale Date", value=datetime.today())
        submit = st.form_submit_button("Add Sale")

        if submit:
            try:
                validate_input(ProductName=product_name, Customer=customer)
                add_record("sales", (product_name, price, quantity, customer, sale_date))
                st.success("Sale added successfully!")
            except ValueError as e:
                st.error(e)

    st.subheader("Sales Records")
    sales_data = fetch_data("sales")
    if not sales_data.empty:
        st.dataframe(sales_data, use_container_width=True)
        generate_csv_download(sales_data, "Sales")
    else:
        st.info("No sales found.")

# Manage Orders
if page == "Manage Orders":
    st.header("Manage Orders")
    with st.form("orders_form"):
        product_name = st.text_input("Product Name")
        quantity = st.number_input("Quantity", min_value=1, step=1)
        status = st.selectbox("Status", ["Pending", "Completed"])
        order_date = st.date_input("Order Date", value=datetime.today())
        submit = st.form_submit_button("Add Order")

        if submit:
            try:
                validate_input(ProductName=product_name)
                add_record("orders", (product_name, quantity, status, order_date))
                st.success("Order added successfully!")
            except ValueError as e:
                st.error(e)

    st.subheader("Order Records")
    order_data = fetch_data("orders")
    if not order_data.empty:
        st.dataframe(order_data, use_container_width=True)
        generate_csv_download(order_data, "Orders")

        # Mark orders as completed
        st.subheader("Update Order Status")
        pending_orders = order_data[order_data["status"] == "Pending"]
        if not pending_orders.empty:
            order_id_to_update = st.selectbox("Select Order ID to Mark as Completed", pending_orders["id"])
            if st.button("Mark as Completed"):
                update_record_status("orders", order_id_to_update, "Completed")
                st.success("Order marked as completed!")
                st.rerun()  # Refresh the app
        else:
            st.info("No pending orders to update.")
    else:
        st.info("No orders found.")
