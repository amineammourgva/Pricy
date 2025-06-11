import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
from io import BytesIO
import sqlite3
from contextlib import closing

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('pricy.db')
    with closing(conn.cursor()) as c:
        # Create products table
        c.execute('''CREATE TABLE IF NOT EXISTS products
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     name TEXT UNIQUE,
                     category TEXT,
                     notes TEXT)''')
        
        # Create concessions table
        c.execute('''CREATE TABLE IF NOT EXISTS concessions
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     name TEXT UNIQUE,
                     location TEXT,
                     notes TEXT)''')
        
        # Create prices table
        c.execute('''CREATE TABLE IF NOT EXISTS prices
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     product_id INTEGER,
                     concession_id INTEGER,
                     price REAL,
                     date DATE,
                     notes TEXT,
                     FOREIGN KEY (product_id) REFERENCES products (id),
                     FOREIGN KEY (concession_id) REFERENCES concessions (id))''')
    conn.commit()
    conn.close()

# Helper functions for database operations
def get_db_connection():
    return sqlite3.connect('pricy.db')

def add_product(name, category, notes):
    with closing(get_db_connection()) as conn:
        c = conn.cursor()
        try:
            c.execute("INSERT INTO products (name, category, notes) VALUES (?, ?, ?)",
                     (name, category, notes))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def add_concession(name, location, notes):
    with closing(get_db_connection()) as conn:
        c = conn.cursor()
        try:
            c.execute("INSERT INTO concessions (name, location, notes) VALUES (?, ?, ?)",
                     (name, location, notes))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def add_price(product, concession, price, date, notes):
    with closing(get_db_connection()) as conn:
        c = conn.cursor()
        # Get product and concession IDs
        c.execute("SELECT id FROM products WHERE name=?", (product,))
        product_id = c.fetchone()[0]
        
        c.execute("SELECT id FROM concessions WHERE name=?", (concession,))
        concession_id = c.fetchone()[0]
        
        c.execute("""INSERT INTO prices (product_id, concession_id, price, date, notes)
                     VALUES (?, ?, ?, ?, ?)""",
                  (product_id, concession_id, price, date, notes))
        conn.commit()

def delete_product(name):
    with closing(get_db_connection()) as conn:
        c = conn.cursor()
        # First delete related prices
        c.execute("DELETE FROM prices WHERE product_id IN (SELECT id FROM products WHERE name=?)", (name,))
        # Then delete the product
        c.execute("DELETE FROM products WHERE name=?", (name,))
        conn.commit()

def delete_concession(name):
    with closing(get_db_connection()) as conn:
        c = conn.cursor()
        # First delete related prices
        c.execute("DELETE FROM prices WHERE concession_id IN (SELECT id FROM concessions WHERE name=?)", (name,))
        # Then delete the concession
        c.execute("DELETE FROM concessions WHERE name=?", (name,))
        conn.commit()

def get_products_df():
    with closing(get_db_connection()) as conn:
        return pd.read_sql("SELECT name as 'Product Name', category as 'Product Category', notes as 'Notes' FROM products", conn)

def get_concessions_df():
    with closing(get_db_connection()) as conn:
        return pd.read_sql("SELECT name as 'Concession Name', location as 'Location Tag', notes as 'Notes' FROM concessions", conn)

def get_prices_df():
    with closing(get_db_connection()) as conn:
        return pd.read_sql("""SELECT p.name as Product, c.name as Concession, 
                                     pr.price as Price, pr.date as Date, pr.notes as Notes
                              FROM prices pr
                              JOIN products p ON pr.product_id = p.id
                              JOIN concessions c ON pr.concession_id = c.id""", conn)

# Initialize database
init_db()

# Main App
st.title("✈️ Pricy")

# Navigation
menu = ["Dashboard", "Product Management", "Concession Management", "Price Entry", "Benchmark View"]
choice = st.sidebar.selectbox("Navigation", menu)

# Dashboard
if choice == "Dashboard":
    st.header("Price Benchmarking Dashboard")
    prices_df = get_prices_df()
    
    if not prices_df.empty:
        # Latest prices
        st.subheader("Latest Prices")
        latest_prices = prices_df.sort_values('Date', ascending=False).drop_duplicates(['Product', 'Concession'])
        st.dataframe(latest_prices)
        
        # Price statistics by product
        st.subheader("Price Statistics by Product")
        stats = prices_df.groupby('Product')['Price'].agg(['mean', 'min', 'max']).reset_index()
        stats.columns = ['Product', 'Average Price', 'Minimum Price', 'Maximum Price']
        st.dataframe(stats)
        
        # Filtering options
        st.subheader("Filter Data")
        col1, col2, col3 = st.columns(3)
        
        products_df = get_products_df()
        concessions_df = get_concessions_df()
        
        with col1:
            product_filter = st.selectbox("Filter by Product", ['All'] + list(products_df['Product Name'].unique()))
        
        with col2:
            concession_filter = st.selectbox("Filter by Concession", ['All'] + list(concessions_df['Concession Name'].unique()))
        
        with col3:
            location_filter = st.selectbox("Filter by Location", ['All', 'Airside', 'Landside', 'City'])
        
        # Apply filters
        filtered_data = prices_df.copy()
        if product_filter != 'All':
            filtered_data = filtered_data[filtered_data['Product'] == product_filter]
        if concession_filter != 'All':
            filtered_data = filtered_data[filtered_data['Concession'] == concession_filter]
        if location_filter != 'All':
            concessions_in_location = concessions_df[
                concessions_df['Location Tag'] == location_filter]['Concession Name']
            filtered_data = filtered_data[filtered_data['Concession'].isin(concessions_in_location)]
        
        st.dataframe(filtered_data)
    else:
        st.warning("No price data available. Please enter some prices first.")

# Product Management
elif choice == "Product Management":
    st.header("Product Management")
    
    tab1, tab2 = st.tabs(["Add Product", "View/Delete Products"])
    
    with tab1:
        with st.form("product_form"):
            name = st.text_input("Product Name*")
            category = st.selectbox("Product Category*", ["Beverage", "Meal", "Snack", "Other"])
            notes = st.text_area("Notes")
            
            if st.form_submit_button("Add Product"):
                if name:
                    if add_product(name, category, notes):
                        st.success(f"Product '{name}' added successfully!")
                    else:
                        st.error(f"Product '{name}' already exists!")
                else:
                    st.error("Product name is required")
    
    with tab2:
        products_df = get_products_df()
        if not products_df.empty:
            st.dataframe(products_df)
            
            product_to_delete = st.selectbox("Select product to delete", 
                                           products_df['Product Name'].unique())
            
            if st.button("Delete Product"):
                delete_product(product_to_delete)
                st.success(f"Product '{product_to_delete}' deleted successfully!")
                st.experimental_rerun()  # Refresh the view
        else:
            st.info("No products added yet.")

# Concession Management
elif choice == "Concession Management":
    st.header("Concession Management")
    
    tab1, tab2 = st.tabs(["Add Concession", "View/Delete Concessions"])
    
    with tab1:
        with st.form("concession_form"):
            name = st.text_input("Concession Name*")
            location = st.selectbox("Location Tag*", ["Airside", "Landside", "City"])
            notes = st.text_area("Notes")
            
            if st.form_submit_button("Add Concession"):
                if name:
                    if add_concession(name, location, notes):
                        st.success(f"Concession '{name}' added successfully!")
                    else:
                        st.error(f"Concession '{name}' already exists!")
                else:
                    st.error("Concession name is required")
    
    with tab2:
        concessions_df = get_concessions_df()
        if not concessions_df.empty:
            st.dataframe(concessions_df)
            
            concession_to_delete = st.selectbox("Select concession to delete", 
                                             concessions_df['Concession Name'].unique())
            
            if st.button("Delete Concession"):
                delete_concession(concession_to_delete)
                st.success(f"Concession '{concession_to_delete}' deleted successfully!")
                st.experimental_rerun()  # Refresh the view
        else:
            st.info("No concessions added yet.")

# Price Entry
elif choice == "Price Entry":
    st.header("Price Entry Form")
    
    products_df = get_products_df()
    concessions_df = get_concessions_df()
    
    if not products_df.empty and not concessions_df.empty:
        with st.form("price_form"):
            product = st.selectbox("Select Product*", products_df['Product Name'].unique())
            concession = st.selectbox("Select Concession*", concessions_df['Concession Name'].unique())
            price = st.number_input("Price*", min_value=0.0, format="%.2f")
            date = st.date_input("Date of Price*", datetime.date.today())
            notes = st.text_area("Notes (e.g., portion size, packaging)")
            
            if st.form_submit_button("Submit Price"):
                add_price(product, concession, price, date, notes)
                st.success("Price submitted successfully!")
    else:
        if products_df.empty:
            st.error("Please add at least one product first.")
        if concessions_df.empty:
            st.error("Please add at least one concession first.")

# Benchmark View
elif choice == "Benchmark View":
    st.header("Price Benchmarking")
    
    prices_df = get_prices_df()
    products_df = get_products_df()
    
    if not prices_df.empty:
        # Product selection
        selected_product = st.selectbox("Select Product to Analyze", 
                                      products_df['Product Name'].unique())
        
        # Filter data for selected product
        product_prices = prices_df[prices_df['Product'] == selected_product]
        
        # Historical price chart
        st.subheader(f"Historical Price Trend for {selected_product}")
        fig = px.line(product_prices, x='Date', y='Price', color='Concession',
                      title=f"Price Trend for {selected_product}")
        st.plotly_chart(fig)
        
        # Latest price comparison
        st.subheader("Latest Price Comparison")
        latest_prices = product_prices.sort_values('Date', ascending=False).drop_duplicates(['Concession'])
        st.dataframe(latest_prices)
        
        # Export options
        st.subheader("Export Data")
        export_format = st.radio("Select export format", ["CSV", "Excel"])
        
        if export_format == "CSV":
            csv = product_prices.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", csv, f"{selected_product}_prices.csv", "text/csv")
        else:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                product_prices.to_excel(writer, index=False, sheet_name='Price Data')
            st.download_button("Download Excel", output.getvalue(), 
                             f"{selected_product}_prices.xlsx", 
                             "application/vnd.ms-excel")
    else:
        st.warning("No price data available. Please enter some prices first.")

# Data persistence instructions
st.sidebar.markdown("---")
st.sidebar.info("""
**Note:** This app now uses SQLite database for persistent storage. 
Data will be saved between sessions.
""")
