import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
from io import BytesIO
from supabase import create_client, Client

# Initialize Supabase client
@st.cache_resource
def init_supabase():
    url = "https://lczakwhqgpwgurbethyl.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxjemFrd2hxZ3B3Z3VyYmV0aHlsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk2Mzc3NjIsImV4cCI6MjA2NTIxMzc2Mn0.hJeo-U_gCC8HCCb_E9-rFpdl0pIXz3DAJJEaIExl6w4"
    return create_client(url, key)

supabase = init_supabase()

# Database helper functions
def add_product(name, category, notes):
    try:
        response = supabase.table("products").insert({
            "name": name,
            "category": category,
            "notes": notes
        }).execute()
        if len(response.data) > 0:
            return True
        return False
    except Exception as e:
        st.error(f"Error adding product: {str(e)}")
        return False

def add_concession(name, location, notes):
    try:
        response = supabase.table("concessions").insert({
            "name": name,
            "location": location,
            "notes": notes
        }).execute()
        if len(response.data) > 0:
            return True
        return False
    except Exception as e:
        st.error(f"Error adding concession: {str(e)}")
        return False

def add_price(product, concession, price, date, notes):
    try:
        # Get product ID
        product_data = supabase.table("products").select("id").eq("name", product).execute()
        if len(product_data.data) == 0:
            st.error("Product not found")
            return False
        
        # Get concession ID
        concession_data = supabase.table("concessions").select("id").eq("name", concession).execute()
        if len(concession_data.data) == 0:
            st.error("Concession not found")
            return False
        
        # Insert price
        response = supabase.table("prices").insert({
            "product_id": product_data.data[0]["id"],
            "concession_id": concession_data.data[0]["id"],
            "price": float(price),
            "date": date.isoformat(),
            "notes": notes
        }).execute()
        
        if len(response.data) > 0:
            return True
        return False
    except Exception as e:
        st.error(f"Error adding price: {str(e)}")
        return False

def delete_product(name):
    try:
        # First delete related prices
        product_data = supabase.table("products").select("id").eq("name", name).execute()
        if len(product_data.data) > 0:
            supabase.table("prices").delete().eq("product_id", product_data.data[0]["id"]).execute()
        
        # Then delete the product
        supabase.table("products").delete().eq("name", name).execute()
        return True
    except Exception as e:
        st.error(f"Error deleting product: {str(e)}")
        return False

def delete_concession(name):
    try:
        # First delete related prices
        concession_data = supabase.table("concessions").select("id").eq("name", name).execute()
        if len(concession_data.data) > 0:
            supabase.table("prices").delete().eq("concession_id", concession_data.data[0]["id"]).execute()
        
        # Then delete the concession
        supabase.table("concessions").delete().eq("name", name).execute()
        return True
    except Exception as e:
        st.error(f"Error deleting concession: {str(e)}")
        return False

def get_products_df():
    try:
        response = supabase.table("products").select("*").execute()
        df = pd.DataFrame(response.data)
        return df.rename(columns={
            "name": "Product Name",
            "category": "Product Category",
            "notes": "Notes"
        })
    except Exception as e:
        st.error(f"Error fetching products: {str(e)}")
        return pd.DataFrame()

def get_concessions_df():
    try:
        response = supabase.table("concessions").select("*").execute()
        df = pd.DataFrame(response.data)
        return df.rename(columns={
            "name": "Concession Name",
            "location": "Location Tag",
            "notes": "Notes"
        })
    except Exception as e:
        st.error(f"Error fetching concessions: {str(e)}")
        return pd.DataFrame()

def get_prices_df():
    try:
        response = supabase.table("prices").select("*, products(name), concessions(name)").execute()
        df = pd.DataFrame(response.data)
        
        # Rename columns for consistency with original app
        if not df.empty:
            df = df.rename(columns={
                "products.name": "Product",
                "concessions.name": "Concession",
                "price": "Price",
                "date": "Date",
                "notes": "Notes"
            })
            df = df[["Product", "Concession", "Price", "Date", "Notes"]]  # Reorder columns
        
        return df
    except Exception as e:
        st.error(f"Error fetching prices: {str(e)}")
        return pd.DataFrame()

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
        # Convert date strings to datetime objects for proper sorting
        prices_df['Date'] = pd.to_datetime(prices_df['Date'])
        
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
                        st.rerun()
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
                if delete_product(product_to_delete):
                    st.success(f"Product '{product_to_delete}' deleted successfully!")
                    st.rerun()
                else:
                    st.error("Failed to delete product")
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
                        st.rerun()
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
                if delete_concession(concession_to_delete):
                    st.success(f"Concession '{concession_to_delete}' deleted successfully!")
                    st.rerun()
                else:
                    st.error("Failed to delete concession")
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
                if add_price(product, concession, price, date, notes):
                    st.success("Price submitted successfully!")
                    st.rerun()
                else:
                    st.error("Failed to submit price")
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
        # Convert date strings to datetime objects for proper sorting
        prices_df['Date'] = pd.to_datetime(prices_df['Date'])
        
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
**Note:** This app now uses Supabase database for persistent storage. 
Data will be saved between sessions.
""")
