import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
from io import BytesIO

# Initialize session state for data storage
if 'products' not in st.session_state:
    st.session_state.products = pd.DataFrame(columns=['Product Name', 'Product Category', 'Notes'])
    
if 'concessions' not in st.session_state:
    st.session_state.concessions = pd.DataFrame(columns=['Concession Name', 'Location Tag', 'Notes'])
    
if 'prices' not in st.session_state:
    st.session_state.prices = pd.DataFrame(columns=['Product', 'Concession', 'Price', 'Date', 'Notes'])

# Helper functions
def add_product(name, category, notes):
    new_product = pd.DataFrame([[name, category, notes]], 
                              columns=['Product Name', 'Product Category', 'Notes'])
    st.session_state.products = pd.concat([st.session_state.products, new_product], ignore_index=True)

def add_concession(name, location, notes):
    new_concession = pd.DataFrame([[name, location, notes]], 
                                 columns=['Concession Name', 'Location Tag', 'Notes'])
    st.session_state.concessions = pd.concat([st.session_state.concessions, new_concession], ignore_index=True)

def add_price(product, concession, price, date, notes):
    new_price = pd.DataFrame([[product, concession, price, date, notes]], 
                            columns=['Product', 'Concession', 'Price', 'Date', 'Notes'])
    st.session_state.prices = pd.concat([st.session_state.prices, new_price], ignore_index=True)

def delete_product(name):
    st.session_state.products = st.session_state.products[st.session_state.products['Product Name'] != name]
    st.session_state.prices = st.session_state.prices[st.session_state.prices['Product'] != name]

def delete_concession(name):
    st.session_state.concessions = st.session_state.concessions[st.session_state.concessions['Concession Name'] != name]
    st.session_state.prices = st.session_state.prices[st.session_state.prices['Concession'] != name]

# Main App
st.title("✈️ Pricy")

# Navigation
menu = ["Dashboard", "Product Management", "Concession Management", "Price Entry", "Benchmark View"]
choice = st.sidebar.selectbox("Navigation", menu)

# Dashboard
if choice == "Dashboard":
    st.header("Price Benchmarking Dashboard")
    
    if not st.session_state.prices.empty:
        # Latest prices
        st.subheader("Latest Prices")
        latest_prices = st.session_state.prices.sort_values('Date', ascending=False).drop_duplicates(['Product', 'Concession'])
        st.dataframe(latest_prices)
        
        # Price statistics by product
        st.subheader("Price Statistics by Product")
        if not st.session_state.prices.empty:
            stats = st.session_state.prices.groupby('Product')['Price'].agg(['mean', 'min', 'max']).reset_index()
            stats.columns = ['Product', 'Average Price', 'Minimum Price', 'Maximum Price']
            st.dataframe(stats)
            
            # Filtering options
            st.subheader("Filter Data")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                product_filter = st.selectbox("Filter by Product", ['All'] + list(st.session_state.products['Product Name'].unique()))
            
            with col2:
                concession_filter = st.selectbox("Filter by Concession", ['All'] + list(st.session_state.concessions['Concession Name'].unique()))
            
            with col3:
                location_filter = st.selectbox("Filter by Location", ['All', 'Airside', 'Landside', 'City'])
            
            # Apply filters
            filtered_data = st.session_state.prices.copy()
            if product_filter != 'All':
                filtered_data = filtered_data[filtered_data['Product'] == product_filter]
            if concession_filter != 'All':
                filtered_data = filtered_data[filtered_data['Concession'] == concession_filter]
            if location_filter != 'All':
                concessions_in_location = st.session_state.concessions[
                    st.session_state.concessions['Location Tag'] == location_filter]['Concession Name']
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
                    add_product(name, category, notes)
                    st.success(f"Product '{name}' added successfully!")
                else:
                    st.error("Product name is required")
    
    with tab2:
        if not st.session_state.products.empty:
            st.dataframe(st.session_state.products)
            
            product_to_delete = st.selectbox("Select product to delete", 
                                           st.session_state.products['Product Name'].unique())
            
            if st.button("Delete Product"):
                delete_product(product_to_delete)
                st.success(f"Product '{product_to_delete}' deleted successfully!")
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
                    add_concession(name, location, notes)
                    st.success(f"Concession '{name}' added successfully!")
                else:
                    st.error("Concession name is required")
    
    with tab2:
        if not st.session_state.concessions.empty:
            st.dataframe(st.session_state.concessions)
            
            concession_to_delete = st.selectbox("Select concession to delete", 
                                             st.session_state.concessions['Concession Name'].unique())
            
            if st.button("Delete Concession"):
                delete_concession(concession_to_delete)
                st.success(f"Concession '{concession_to_delete}' deleted successfully!")
        else:
            st.info("No concessions added yet.")

# Price Entry
elif choice == "Price Entry":
    st.header("Price Entry Form")
    
    if not st.session_state.products.empty and not st.session_state.concessions.empty:
        with st.form("price_form"):
            product = st.selectbox("Select Product*", st.session_state.products['Product Name'].unique())
            concession = st.selectbox("Select Concession*", st.session_state.concessions['Concession Name'].unique())
            price = st.number_input("Price*", min_value=0.0, format="%.2f")
            date = st.date_input("Date of Price*", datetime.date.today())
            notes = st.text_area("Notes (e.g., portion size, packaging)")
            
            if st.form_submit_button("Submit Price"):
                add_price(product, concession, price, date, notes)
                st.success("Price submitted successfully!")
    else:
        if st.session_state.products.empty:
            st.error("Please add at least one product first.")
        if st.session_state.concessions.empty:
            st.error("Please add at least one concession first.")

# Benchmark View
elif choice == "Benchmark View":
    st.header("Price Benchmarking")
    
    if not st.session_state.prices.empty:
        # Product selection
        selected_product = st.selectbox("Select Product to Analyze", 
                                      st.session_state.products['Product Name'].unique())
        
        # Filter data for selected product
        product_prices = st.session_state.prices[st.session_state.prices['Product'] == selected_product]
        
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
**Note:** This app uses session storage. Data will be lost when the browser is closed. 
For permanent storage, export your data regularly.
""")
