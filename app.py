import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import streamlit.components.v1 as components
import time
import json
import cv2
import numpy as np
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration
from typing import List, NamedTuple
import av
from pyzbar.pyzbar import decode

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
if 'active_scanner' not in st.session_state:
    st.session_state.active_scanner = None

# Define RTC configuration (use Google's STUN server)
rtc_configuration = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

# Barcode detection result class
class BarcodeResult(NamedTuple):
    barcode_value: str
    bounding_box: List[List[int]]

# Video processor for barcode detection
class BarcodeVideoProcessor(VideoProcessorBase):
    def __init__(self, target_field):
        self.target_field = target_field
        self.result_queue = []
        self.last_barcode = None
        self.barcode_detected = False
        
    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        
        # Detect barcodes
        barcodes = decode(img)
        
        # Process detected barcodes
        self.barcode_detected = False
        for barcode in barcodes:
            # Extract barcode value and bounding box
            barcode_value = barcode.data.decode("utf-8")
            
            # Don't process the same barcode repeatedly
            if self.last_barcode == barcode_value:
                continue
                
            self.last_barcode = barcode_value
            self.barcode_detected = True
            
            # Draw bounding box
            points = barcode.polygon
            if len(points) > 0:
                pts = np.array([[(p.x, p.y) for p in points]], dtype=np.int32)
                cv2.polylines(img, pts, True, (0, 255, 0), 2)
            
            # Draw barcode value
            x, y, w, h = barcode.rect
            cv2.putText(
                img, 
                barcode_value, 
                (x, y - 10), 
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5, 
                (0, 255, 0), 
                2
            )
            
            # Add to result queue
            self.result_queue.append(barcode_value)
            
            # Update session state based on target field
            if self.target_field == "sku":
                st.session_state.scanned_sku = barcode_value
            elif self.target_field == "part_number":
                st.session_state.scanned_part_number = barcode_value
        
        return av.VideoFrame.from_ndarray(img, format="bgr24")

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
    
    # Add barcode scanner for SKU
    st.write("Or scan barcode:")
    
    sku_scanner_col1, sku_scanner_col2 = st.columns([1, 1])
    with sku_scanner_col1:
        sku_scanner_placeholder = st.empty()
        if st.button("Scan SKU", key="scan_sku_btn"):
            st.session_state.active_scanner = "sku"
            st.rerun()
    
    # Manufacturer input
    manufacturer = st.text_input("Manufacturer (e.g., Siemens, Schneider, Pils)", key="manufacturer_input", value="")
    
    # Manufacturer part number input with barcode scanner
    st.subheader("Manufacturer Part Number")
    part_number = st.text_input("Enter Manufacturer Part Number manually (e.g., L24DF3)", key="part_number_input", value=st.session_state.scanned_part_number)
    
    # Add barcode scanner for Manufacturer Part Number
    st.write("Or scan barcode:")
    
    pn_scanner_col1, pn_scanner_col2 = st.columns([1, 1])
    with pn_scanner_col1:
        pn_scanner_placeholder = st.empty()
        if st.button("Scan Part Number", key="scan_pn_btn"):
            st.session_state.active_scanner = "part_number"
            st.rerun()
    
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

# Display active scanner outside the form
if st.session_state.active_scanner == "sku":
    st.subheader("SKU Barcode Scanner")
    scanner = webrtc_streamer(
        key="sku_scanner",
        video_processor_factory=lambda: BarcodeVideoProcessor(target_field="sku"),
        rtc_configuration=rtc_configuration,
        media_stream_constraints={"video": True, "audio": False},
    )
    
    if scanner.state.playing:
        st.write("Scanning for barcodes... Point your camera at a barcode.")
    
    if st.button("Stop Scanner & Use Value"):
        st.session_state.active_scanner = None
        st.rerun()

elif st.session_state.active_scanner == "part_number":
    st.subheader("Part Number Barcode Scanner")
    scanner = webrtc_streamer(
        key="part_number_scanner",
        video_processor_factory=lambda: BarcodeVideoProcessor(target_field="part_number"),
        rtc_configuration=rtc_configuration,
        media_stream_constraints={"video": True, "audio": False},
    )
    
    if scanner.state.playing:
        st.write("Scanning for barcodes... Point your camera at a barcode.")
    
    if st.button("Stop Scanner & Use Value"):
        st.session_state.active_scanner = None
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
        file_name="barcode_entries.csv",
        mime="text/csv"
    ) 