import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import streamlit.components.v1 as components
import time
import json
import base64
from barcode_scanner import html5_qr_scanner

# Display app header
st.title("Barcode Data Entry System")

# Initialize session state variables
if 'form_submitted' not in st.session_state:
    st.session_state.form_submitted = False
if 'scanned_sku' not in st.session_state:
    st.session_state.scanned_sku = ""
if 'scanned_part_number' not in st.session_state:
    st.session_state.scanned_part_number = ""
if 'page' not in st.session_state:
    st.session_state.page = "main"
if 'scan_target' not in st.session_state:
    st.session_state.scan_target = None
if 'last_scanned_value' not in st.session_state:
    st.session_state.last_scanned_value = None

# Check URL parameters for scanned values
if "barcode" in st.query_params and "target" in st.query_params:
    barcode = st.query_params["barcode"]
    target = st.query_params["target"]
    
    if target == "SKU":
        st.session_state.scanned_sku = barcode
    elif target == "PART_NUMBER":
        st.session_state.scanned_part_number = barcode
    
    # Clear parameters
    del st.query_params["barcode"]
    del st.query_params["target"]
    st.session_state.page = "main"
    st.rerun()

# Initialize connection
@st.cache_resource
def init_connection():
    try:
        # Create SQLAlchemy connection string
        password = quote_plus(st.secrets["database"]["db_password"])  # URL encode the password
        conn_str = f"mssql+pymssql://VDRSAdmin:{password}@vdrsapps.database.windows.net/{st.secrets['database']['db_database']}"
        
        # Create engine
        engine = create_engine(conn_str)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            
        return engine
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        return None

# Get table name from secrets
try:
    TABLE_NAME = st.secrets["database"]["db_table"]
except:
    TABLE_NAME = "StockOfParts"

# Perform query
def run_query(query, params=None):
    engine = init_connection()
    if not engine:
        return None
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params if params else {})
            conn.commit()
            
            if query.strip().upper().startswith("SELECT"):
                columns = result.keys()
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
                return rows
            return True
            
    except Exception as e:
        st.error(f"Query error: {str(e)}")
        return None

# Create table if it doesn't exist
def create_table():
    query = f"""
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = '{TABLE_NAME}')
    BEGIN
        CREATE TABLE {TABLE_NAME} (
            SKU VARCHAR(255),
            manufacturer VARCHAR(255),
            manufacturer_part_number VARCHAR(255),
            is_duplicate VARCHAR(255)
        )
    END
    """
    return run_query(query)

# Helper function to get all existing SKUs
def get_all_skus():
    query = f"SELECT SKU FROM {TABLE_NAME}"
    result = run_query(query)
    if result:
        # Convert all SKUs to lowercase strings and strip whitespace
        return [str(row['SKU']).strip().lower() for row in result]
    return []

# Insert new entry
def insert_entry(sku, manufacturer, part_number):
    try:
        # DIRECT SQL APPROACH - Use a CASE statement in the INSERT query itself
        # This will set is_duplicate based on whether the SKU already exists in the table
        insert_query = f"""
        INSERT INTO {TABLE_NAME} (SKU, manufacturer, manufacturer_part_number, is_duplicate) 
        VALUES (
            :sku, 
            :manufacturer, 
            :part_number, 
            CASE 
                WHEN EXISTS (SELECT 1 FROM {TABLE_NAME} WHERE SKU = :sku) THEN 'yes' 
                ELSE 'no' 
            END
        )
        """
        
        success = run_query(insert_query, {
            "sku": sku,
            "manufacturer": manufacturer,
            "part_number": part_number
        })
        
        return success
    except Exception as e:
        st.error(f"Error inserting entry: {str(e)}")
        return False

# Get all entries
def get_all_entries():
    query = f"SELECT * FROM {TABLE_NAME}"
    try:
        result = run_query(query)
        if result:
            return pd.DataFrame(result)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error getting entries: {str(e)}")
        return pd.DataFrame()

# Create the table if it doesn't exist
create_table()

# If form was just submitted successfully, clear the session state
if st.session_state.form_submitted:
    st.session_state.form_submitted = False
    st.rerun()

# Function to handle navigation
def go_to_scanner(target):
    st.session_state.scan_target = target
    st.session_state.page = "scanner"
    st.rerun()

def go_to_main():
    st.session_state.page = "main"
    st.rerun()

def set_scanned_value(value):
    if st.session_state.scan_target == "SKU":
        st.session_state.scanned_sku = value
    else:
        st.session_state.scanned_part_number = value
    st.session_state.page = "main"
    st.rerun()

# Main application logic with page routing
if st.session_state.page == "main":
    st.subheader("Enter part information manually or scan barcodes")
    
    # Create form for data entry
    with st.form("data_entry_form"):
        # SKU input with scan button
        st.subheader("SKU")
        col1, col2 = st.columns([3, 1])
        with col1:
            sku = st.text_input("SKU (e.g., 999.000.932)", key="sku_input", value=st.session_state.scanned_sku)
        with col2:
            st.write("")
            st.write("")
            scan_sku = st.form_submit_button("📷 Scan SKU")
        
        # Manufacturer input
        manufacturer = st.text_input("Manufacturer (e.g., Siemens, Schneider, Pils)", key="manufacturer_input", value="")
        
        # Manufacturer part number input with scan button
        st.subheader("Manufacturer Part Number")
        col1, col2 = st.columns([3, 1])
        with col1:
            part_number = st.text_input("Part Number (e.g., L24DF3)", key="part_number_input", value=st.session_state.scanned_part_number)
        with col2:
            st.write("")
            st.write("")
            scan_part = st.form_submit_button("📷 Scan Part #")
        
        # Submit button
        submit_button = st.form_submit_button("Submit")
        
        if submit_button:
            if not sku or not manufacturer or not part_number:
                st.error("Please fill in all fields.")
            else:
                if insert_entry(sku, manufacturer, part_number):
                    st.success("Data saved successfully!")
                    # Clear the scanned values after submission
                    st.session_state.scanned_sku = ""
                    st.session_state.scanned_part_number = ""
                    st.session_state.form_submitted = True
                    st.rerun()
        
        if scan_sku:
            go_to_scanner("SKU")
            
        if scan_part:
            go_to_scanner("PART_NUMBER")
    
    # Display entries
    df = get_all_entries()
    if not df.empty:
        st.subheader("Database Entries")
        st.dataframe(df)
        
        # Add a button to download as CSV
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download Data as CSV",
            data=csv,
            file_name="barcode_entries.csv",
            mime="text/csv"
        )

elif st.session_state.page == "scanner":
    st.subheader(f"Scanning {st.session_state.scan_target}")
    
    # Scanner container
    with st.container():
        # Show the scanner using the improved module
        html5_qr_scanner()
        
        # Manual entry for scanned value
        scanned_value = st.text_input("Enter the scanned value:", key="scanned_value_input")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Use This Value", key="use_value"):
                if scanned_value:
                    set_scanned_value(scanned_value)
        with col2:
            if st.button("Cancel", key="cancel_scan"):
                go_to_main()
                
        st.info("After scanning, the value will be automatically used. If not, enter it manually and click 'Use This Value'") 