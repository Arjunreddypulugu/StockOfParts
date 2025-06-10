import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import cv2
import numpy as np
from pyzbar.pyzbar import decode
from PIL import Image
import io

# Display app header
st.title("Barcode Data Entry System")

# Initialize session state variables
if 'scanned_sku' not in st.session_state:
    st.session_state.scanned_sku = ""
if 'scanned_part_number' not in st.session_state:
    st.session_state.scanned_part_number = ""

# Initialize connection
@st.cache_resource
def init_connection():
    try:
        password = quote_plus(st.secrets["database"]["db_password"])
        conn_str = f"mssql+pymssql://VDRSAdmin:{password}@vdrsapps.database.windows.net/{st.secrets['database']['db_database']}"
        engine = create_engine(conn_str)
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

# Helper function to get all existing SKUs
def get_all_skus():
    query = f"SELECT SKU FROM {TABLE_NAME}"
    result = run_query(query)
    if result:
        return [str(row['SKU']).strip().lower() for row in result]
    return []

# Insert new entry
def insert_entry(sku, manufacturer, part_number):
    try:
        all_skus = get_all_skus()
        is_duplicate = 'yes' if sku.strip().lower() in all_skus else 'no'
        insert_query = f"""
        INSERT INTO {TABLE_NAME} (SKU, manufacturer, manufacturer_part_number, is_duplicate) 
        VALUES (:sku, :manufacturer, :part_number, :is_duplicate)
        """
        success = run_query(insert_query, {
            "sku": sku,
            "manufacturer": manufacturer,
            "part_number": part_number,
            "is_duplicate": is_duplicate
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

def decode_barcode(image):
    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Decode barcodes
    barcodes = decode(gray)
    
    if barcodes:
        # Return the first barcode data
        return barcodes[0].data.decode('utf-8')
    return None

# Main form
st.subheader("Enter part information manually or scan barcodes")

with st.form("data_entry_form"):
    # SKU input with scan button
    st.subheader("SKU")
    col1, col2 = st.columns([3, 1])
    with col1:
        sku = st.text_input("SKU (e.g., 999.000.932)", key="sku_input", value=st.session_state.scanned_sku)
    with col2:
        st.write("")
        st.write("")
        if st.form_submit_button("📷 Scan SKU"):
            st.session_state.scanning = "SKU"
            st.rerun()
    
    # Manufacturer input
    manufacturer = st.text_input("Manufacturer (e.g., Siemens, Schneider, Pils)", key="manufacturer_input")
    
    # Manufacturer part number input with scan button
    st.subheader("Manufacturer Part Number")
    col1, col2 = st.columns([3, 1])
    with col1:
        part_number = st.text_input("Part Number (e.g., L24DF3)", key="part_number_input", value=st.session_state.scanned_part_number)
    with col2:
        st.write("")
        st.write("")
        if st.form_submit_button("📷 Scan Part #"):
            st.session_state.scanning = "PART_NUMBER"
            st.rerun()
    
    # Submit button
    if st.form_submit_button("Submit"):
        if not sku or not manufacturer or not part_number:
            st.error("Please fill in all fields.")
        else:
            if insert_entry(sku, manufacturer, part_number):
                st.success("Data saved successfully!")
                st.session_state.scanned_sku = ""
                st.session_state.scanned_part_number = ""
                st.rerun()

# Handle barcode scanning
if 'scanning' in st.session_state:
    st.subheader(f"Scanning {st.session_state.scanning}")
    
    # Camera input
    camera_input = st.camera_input("Take a picture of the barcode")
    
    if camera_input is not None:
        # Convert the image to bytes
        image_bytes = camera_input.getvalue()
        
        # Convert to numpy array
        image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        
        # Decode barcode
        barcode_data = decode_barcode(image)
        
        if barcode_data:
            if st.session_state.scanning == "SKU":
                st.session_state.scanned_sku = barcode_data
            else:
                st.session_state.scanned_part_number = barcode_data
            st.session_state.scanning = None
            st.rerun()
        else:
            st.error("No barcode detected. Please try again.")
    
    if st.button("Cancel"):
        st.session_state.scanning = None
        st.rerun()

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
        file_name="barcode_data.csv",
        mime="text/csv"
    ) 