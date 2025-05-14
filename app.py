import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import streamlit.components.v1 as components
import time
import json
import base64

# Display app header
st.title("Barcode Data Entry System")
st.subheader("Enter part information manually or scan barcodes")

# Initialize session state variables
if 'form_submitted' not in st.session_state:
    st.session_state.form_submitted = False
if 'scanned_sku' not in st.session_state:
    st.session_state.scanned_sku = ""
if 'scanned_part_number' not in st.session_state:
    st.session_state.scanned_part_number = ""
if 'current_scan_target' not in st.session_state:
    st.session_state.current_scan_target = None
if 'show_scanner' not in st.session_state:
    st.session_state.show_scanner = False
if 'last_scan' not in st.session_state:
    st.session_state.last_scan = None

# Callback functions for barcode scanning
def start_scanning(target):
    st.session_state.current_scan_target = target
    st.session_state.show_scanner = True
    st.rerun()

def stop_scanning():
    st.session_state.show_scanner = False
    st.session_state.current_scan_target = None
    st.rerun()

def use_scanned_value(value):
    if st.session_state.current_scan_target == "SKU":
        st.session_state.scanned_sku = value
    elif st.session_state.current_scan_target == "PART_NUMBER":
        st.session_state.scanned_part_number = value
    
    st.session_state.show_scanner = False
    st.session_state.current_scan_target = None
    st.session_state.last_scan = None
    st.rerun()

# Simple barcode scanner HTML/JS component
def barcode_scanner():
    return """
    <div style="margin-bottom: 20px;">
        <div id="reader" style="width: 100%;"></div>
        <div id="scanned-result" style="margin-top: 10px; font-weight: bold;"></div>
    </div>

    <script src="https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"></script>
    <script>
        // Initialize scanner
        const html5QrCode = new Html5Qrcode("reader");
        const scannedResult = document.getElementById('scanned-result');
        
        // Start scanning
        html5QrCode.start(
            { facingMode: "environment" }, 
            {
                fps: 10,
                qrbox: 250
            },
            (decodedText, decodedResult) => {
                console.log(`Scan result: ${decodedText}`, decodedResult);
                html5QrCode.stop();
                
                // Display the scanned result
                scannedResult.innerText = `Scanned: ${decodedText}`;
                
                // Store the value in localStorage for display purposes only
                localStorage.setItem('lastScannedValue', decodedText);
                
                // No need to try to communicate with Streamlit - we'll use manual confirmation
            },
            (errorMessage) => {
                console.log(`QR Code scanning error: ${errorMessage}`);
            }
        ).catch((err) => {
            console.log(`Unable to start scanner: ${err}`);
        });
    </script>
    """

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
        
        # Debug: Print the full table after insert
        if success:
            st.write("Insert successful!")
            full_table_query = f"SELECT * FROM {TABLE_NAME}"
            full_table = run_query(full_table_query)
            st.write("Full table after insert:", full_table)
        
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

# Create form for data entry
with st.form("data_entry_form"):
    # SKU input with barcode scanner
    st.subheader("SKU")
    sku = st.text_input("Enter SKU manually (e.g., 999.000.932)", key="sku_input", value=st.session_state.scanned_sku)
    
    # Manufacturer input
    manufacturer = st.text_input("Manufacturer (e.g., Siemens, Schneider, Pils)", key="manufacturer_input", value="")
    
    # Manufacturer part number input with barcode scanner
    st.subheader("Manufacturer Part Number")
    part_number = st.text_input("Enter Manufacturer Part Number manually (e.g., L24DF3)", key="part_number_input", value=st.session_state.scanned_part_number)
    
    # Submit button
    col1, col2, col3 = st.columns(3)
    with col1:
        submit_button = st.form_submit_button("Submit")
    with col2:
        scan_sku_button = st.form_submit_button("Scan SKU", type="primary")
    with col3:
        scan_part_button = st.form_submit_button("Scan Part #", type="primary")
    
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
    
    if scan_sku_button:
        st.session_state.current_scan_target = "SKU"
        st.session_state.show_scanner = True
        st.rerun()
        
    if scan_part_button:
        st.session_state.current_scan_target = "PART_NUMBER"
        st.session_state.show_scanner = True
        st.rerun()

# Show scanner if activated
if st.session_state.show_scanner:
    st.subheader(f"Scanning for {st.session_state.current_scan_target}")
    
    # Scanner container
    scanner_container = st.container()
    with scanner_container:
        # Show the scanner
        components.html(barcode_scanner(), height=400)
        
        # Manual entry for scanned value
        st.write("### Enter the scanned barcode value:")
        scanned_value = st.text_input("Scanned value", key="manual_scan_value")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Use This Value", key="use_value"):
                if scanned_value:
                    use_scanned_value(scanned_value)
        with col2:
            if st.button("Cancel", key="cancel_scan"):
                stop_scanning()
                
        st.info("After scanning, enter the value shown above in the 'Scanned value' field and click 'Use This Value'")

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